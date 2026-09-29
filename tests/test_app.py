from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from knowledge_assistant.ingestion import build_seed_chunks


def test_failed_answer_displays_retrieved_sources_and_regenerate(monkeypatch):
    chunk = build_seed_chunks()[0]
    citation = {"chunk_id": chunk.chunk_id, "section_title": chunk.section_title,
                "source": chunk.source_file, "system_version": "legacy", "source_type": "doc",
                "details": chunk.text, "excerpt_start": 0, "excerpt_end": 10}
    result = {"status": "error", "summary": "Retrieved evidence; validation failed.",
              "evidence": [], "retrieved_evidence": [citation],
              "diagnostics": {"stage": "validation", "retrieved_chunks": 1}}
    fake = SimpleNamespace(chunks=[chunk], provider_error="", answer_question=lambda *args: result)
    monkeypatch.setattr("knowledge_assistant.core.KnowledgeAssistant", lambda: fake)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    app.chat_input[0].set_value("What changed?").run()
    assert not app.exception
    assert app.error[0].value == result["summary"]
    assert any("Retrieved sources" in m.value for m in app.markdown)
    assert any("start=0&amp;end=10" in m.value and 'target="_blank"' in m.value for m in app.markdown)
    app.run()
    assert any(button.label == "Regenerate answer" for button in app.button)


def test_document_viewer_highlights_only_passage_and_retains_full_document(monkeypatch, tmp_path):
    path = tmp_path / "document.txt"
    path.write_text("Before context.\nIndexed section with <markup>.\nAfter context.", encoding="utf-8")
    chunk = replace(build_seed_chunks()[0], source_file=str(path), text="Indexed section with <markup>.")
    fake = SimpleNamespace(chunks=[chunk], provider_error="")
    monkeypatch.setattr("knowledge_assistant.core.KnowledgeAssistant", lambda: fake)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.query_params.update(citation=chunk.chunk_id, start="0", end="15")
    app.run()
    assert not app.exception
    document = next(m.value for m in app.markdown if 'class="document-text"' in m.value)
    assert "Before context." in document and "After context." in document
    assert '<mark class="indexed-section">Indexed section</mark>' in document
    assert "&lt;markup&gt;" in document
