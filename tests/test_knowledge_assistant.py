from knowledge_assistant.core import KnowledgeAssistant
from knowledge_assistant.llm_provider import ProviderConfig


def test_conflict_question_without_model_does_not_fabricate_summary():
    assistant = KnowledgeAssistant(provider_config=ProviderConfig())
    answer = assistant.answer_question("Why does the surcharge logic look inconsistent for accounts near 1000 kWh?")

    assert answer["status"] == "error"
    assert answer["evidence"] == []
    assert answer["retrieved_evidence"]
    assert answer["risk_map"] == {}


def test_gap_question_flags_missing_coverage():
    assistant = KnowledgeAssistant(provider_config=ProviderConfig())
    answer = assistant.answer_question("How does the AMI meter integration handle retry logic?")

    assert answer["status"] == "error"
    assert answer["risk_level"] == "unknown"
    assert answer["summary"]
    assert answer["risk_map"] == {}
