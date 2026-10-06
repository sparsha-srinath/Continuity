import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from knowledge_assistant.core import KnowledgeAssistant
from knowledge_assistant.ingestion import build_seed_chunks
from knowledge_assistant.llm_provider import ProviderConfig, ProviderError, generate_text, load_provider_config
from knowledge_assistant.retrieval import split_chunks
from knowledge_assistant.vector_store import ChromaKnowledgeStore


QUESTION = "What changed about license renewal between the legacy and modernized systems?"


@pytest.fixture
def assistant():
    # The model and vector server are not required for unit-level contract checks.
    store = SimpleNamespace(index_chunks=Mock(), query=Mock(return_value={"ids": [[]]}))
    return KnowledgeAssistant(
        provider_config=ProviderConfig(), store=store,
        metadata_store=SimpleNamespace(record_query=Mock()),
    )


@pytest.mark.parametrize("question,scope", [
    (QUESTION, "compare"),
    ("Does the multi-year renewal discount apply to type C licenses?", "legacy"),
    ("Does the multi-year renewal discount apply to type C licenses?", "mod_v1"),
    ("Why did type C renewals get charged different fees?", "legacy"),
    ("Why does the surcharge logic differ near 1000 kWh?", "legacy"),
    ("How does the AMI meter integration handle retry logic?", "legacy"),
])
def test_no_canned_answer_without_a_provider(assistant, question, scope):
    result = assistant.answer_question(question, scope)
    assert result["status"] == "error"
    assert result["diagnostics"]["stage"] == "configuration"
    assert result["evidence"] == []
    assert result["retrieved_evidence"]


def test_comparison_retrieval_and_context_retain_implementations(assistant):
    candidates = assistant._retrieve_candidates(QUESTION)
    selected, system, user, schema, budget = assistant._prepare_context(QUESTION, candidates, "compare")
    assert {"BLPTS-LEGACY-FEE", "MOD-CODE-FEE", "MOD-CODE-DISCOUNT"} <= {
        c["chunk_id"].split("::part-")[0] for c in selected
    }
    assert any("def calculate_multi_year_total" in c["text"] for c in selected)
    assert {c["system_version"] for c in selected} == {"legacy", "mod_v1"}
    assert len((system + user).encode("utf-8")) <= budget
    assert schema["properties"]["citations"]["items"]["enum"] == list(range(len(selected)))
    assert all(len(c.text) <= 1800 for c in assistant.chunks)
    for source in selected:
        original = next(c.text for c in assistant.chunks if c.chunk_id == source["chunk_id"])
        assert original[source["excerpt_start"]:source["excerpt_end"]] == source["text"]


def test_version_scope_never_leaks_modernized_records(assistant):
    seen = []
    def generator(question, context, scope):
        seen.extend(context)
        return json.dumps({"summary": "The supplied evidence does not establish a discount.",
                           "citations": [0], "insufficient_evidence": True})
    assistant.answer_generator = generator
    result = assistant.answer_question("Does the multi-year renewal discount apply to type C licenses?", "legacy")
    assert seen and all(c["system_version"] == "legacy" for c in seen)
    assert result["status"] == "gap"


def test_empty_retrieval_does_not_call_model(assistant):
    assistant.answer_generator = Mock()
    result = assistant.answer_question("What changed about Neptune submarine maintenance?")
    assert result["status"] == "unsupported"
    assert result["diagnostics"]["stage"] == "retrieval"
    assistant.answer_generator.assert_not_called()


def test_invalid_shape_retries_same_evidence_then_accepts_model_answer(assistant):
    contexts = []
    summary = "Legacy: the cited source describes an earlier path. Modernized: the cited source describes the replacement."
    def generator(query, context, scope):
        contexts.append(context)
        if len(contexts) == 1:
            # Actual failure reproduced from Qwen when the old prompt was truncated.
            return json.dumps({"ref": 1, "source": "a.py", "text": "an evidence-shaped object"})
        return json.dumps({"summary": summary, "citations": [0, 1], "insufficient_evidence": False})
    assistant.answer_generator = generator
    result = assistant.answer_question(QUESTION)
    assert contexts[0] == contexts[1]
    assert result["summary"] == summary
    assert result["status"] == "versioned"
    assert result["diagnostics"]["attempts"] == 2
    assert result["generation_method"] == "model"


@pytest.mark.parametrize("reference", [-1, 999, True, 1.5, "1", "NOT-RETRIEVED"])
def test_invalid_references_fail_closed_and_preserve_retrieved_sources(assistant, reference):
    assistant.answer_generator = Mock(return_value=json.dumps({
        "summary": "Legacy: an unsupported claim. Modernized: another claim.",
        "citations": [reference], "insufficient_evidence": False,
    }))
    result = assistant.answer_question(QUESTION)
    assert result["status"] == "error"
    assert result["evidence"] == []
    assert result["retrieved_evidence"]
    assert result["diagnostics"]["stage"] == "validation"
    assert assistant.answer_generator.call_count == 2


@pytest.mark.parametrize("raw", ["[]", "null", "42", '{"summary":[],"citations":[0]}', '{"summary":"No citations"}'])
def test_bad_json_shapes_do_not_crash_or_fall_back(assistant, raw):
    assistant.answer_generator = Mock(return_value=raw)
    result = assistant.answer_question(QUESTION)
    assert result["status"] == "error"
    assert result["diagnostics"]["stage"] == "validation"
    assert result["evidence"] == []


def test_citations_must_come_from_sent_context_not_just_retrieval(assistant):
    candidates = assistant._retrieve_candidates(QUESTION)
    assistant.answer_generator = Mock(return_value=json.dumps({
        "summary": "Legacy only.", "citations": [candidates[1]["chunk_id"]],
    }))
    selected = [candidates[0]]
    system, user, schema = assistant._prompts("instructions ", QUESTION, selected, "legacy")
    assistant._prepare_context = Mock(return_value=(selected, system, user, schema, 10000))
    result = assistant._generate_answer(QUESTION, candidates, "legacy")
    assert result["status"] == "error"
    assert "citation not present" in result["diagnostics"]["error"]


def test_comparison_requires_both_available_versions(assistant):
    assistant.answer_generator = Mock(return_value=json.dumps({
        "summary": "Legacy: earlier. Modernized: later.", "citations": [0],
    }))
    result = assistant.answer_question(QUESTION)
    assert result["status"] == "error"
    assert "both available systems" in result["diagnostics"]["error"]


def test_provider_exception_is_distinct_from_missing_evidence(assistant, monkeypatch):
    assistant.provider_config = ProviderConfig(provider="local")
    call = Mock(side_effect=ProviderError("Connection refused"))
    monkeypatch.setattr("knowledge_assistant.core.generate_text", call)
    result = assistant.answer_question(QUESTION)
    assert result["status"] == "error"
    assert result["diagnostics"]["stage"] == "generation"
    assert result["retrieved_evidence"]
    assert call.call_count == 1


def test_chunking_keeps_late_content_and_exact_source_text(assistant):
    original = assistant.chunks[0]
    document = ("Introductory material.\n" * 150) + "\nSpecialized zebra migration policy.\n"
    parts = split_chunks([replace(original, text=document)])
    assert "".join(part.text for part in parts) == document
    assert len({p.chunk_id for p in parts}) == len(parts)
    assert parts[0].chunk_id == original.chunk_id
    assert all(len(p.text) <= 1800 for p in parts)
    assistant.chunks = parts
    assert any("zebra" in c["text"] for c in assistant._retrieve_candidates("zebra migration policy", "legacy"))


def test_unicode_context_budget_preserves_exact_passages(assistant):
    original = assistant.chunks[0]
    assistant.chunks = split_chunks([replace(original, text="東京 規則 " * 800 + " policy")])
    candidates = assistant._retrieve_candidates("policy", "legacy")
    selected, system, user, _, budget = assistant._prepare_context("policy", candidates, "legacy")
    assert len((system + user).encode("utf-8")) <= budget
    assert all(c["text"] in original.text or c["text"] in assistant.chunks[-1].text for c in selected)


def test_chroma_index_migration_is_non_destructive(tmp_path):
    store = ChromaKnowledgeStore(persist_directory=str(tmp_path))
    chunks = build_seed_chunks()
    store.index_chunks(chunks)
    assert store.collection.count() == len(chunks)
    result = store.query("renewal", top_k=5, system_version="mod_v1")
    ids = set(result["ids"][0])
    assert ids <= {c.chunk_id for c in chunks if c.system_version == "mod_v1"}
    assert store.query("anything", top_k=0)["ids"] == [[]]


def test_provider_config_has_context_and_no_local_key_requirement():
    config = load_provider_config(environ={"LLM_PROVIDER": "local"}, secrets={})
    assert config.api_key == ""
    assert config.uses_ollama
    assert config.context_tokens == 8192
    assert config.max_output_tokens == 600
    with pytest.raises(ProviderError):
        load_provider_config(environ={"LLM_PROVIDER": "openai"}, secrets={})
    with pytest.raises(ProviderError):
        generate_text(ProviderConfig(), "system", "question")


def test_ollama_request_sends_schema_context_and_output_limit(monkeypatch):
    from knowledge_assistant import llm_provider
    captured = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps({"message": {"content": '{"summary":"Test","citations":[0]}'}, "done_reason": "stop"}).encode()
    def urlopen(request, timeout):
        captured.append((request.full_url, json.loads(request.data), timeout))
        return Response()
    monkeypatch.setattr(llm_provider.urllib.request, "urlopen", urlopen)
    config = load_provider_config(environ={"LLM_PROVIDER": "local"}, secrets={})
    schema = KnowledgeAssistant._schema(2)
    generate_text(config, "system", "question", response_schema=schema)
    url, payload, _ = captured[0]
    assert url == "http://localhost:11434/api/chat"
    assert payload["format"] == schema
    assert payload["options"]["num_ctx"] == 8192
    assert payload["options"]["num_predict"] == 600


def test_compatible_endpoint_can_be_selected_explicitly(monkeypatch):
    from knowledge_assistant import llm_provider
    captured = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"choices":[{"message":{"content":"{}"},"finish_reason":"stop"}]}'
    def urlopen(request, timeout):
        captured.append((request.full_url, json.loads(request.data)))
        return Response()
    monkeypatch.setattr(llm_provider.urllib.request, "urlopen", urlopen)
    config = ProviderConfig(provider="local", base_url="http://localhost:11434/v1", local_api="compatible")
    generate_text(config, "system", "question", response_schema=KnowledgeAssistant._schema(2))
    assert captured[0][0].endswith("/v1/chat/completions")
    assert captured[0][1]["response_format"]["type"] == "json_schema"


@pytest.mark.parametrize("payload,provider", [
    ({"message": {"content": "{}"}, "done_reason": "length"}, "ollama"),
    ({"choices": [{"message": {"content": "{}"}, "finish_reason": "length"}]}, "local"),
    ({"choices": [{"message": {"content": None}}]}, "local"),
])
def test_truncated_or_empty_responses_are_provider_errors(payload, provider):
    from knowledge_assistant.llm_provider import _response_text
    with pytest.raises(ProviderError):
        _response_text(payload, provider)
