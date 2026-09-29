from pathlib import Path
from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from knowledge_assistant.demo import DemoAssistant, SCENARIOS


APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_scenarios_resolve_real_passages_and_version_scopes():
    assistant = DemoAssistant()
    chunks = {chunk.chunk_id: chunk for chunk in assistant.chunks}
    for scenario in SCENARIOS:
        result = assistant.present(scenario)
        assert result["status"] == scenario.status
        assert result["generation_method"] == "prepared_demo"
        assert len(result["evidence"]) == len(scenario.sources)
        for source in result["evidence"]:
            assert source["details"] == chunks[source["chunk_id"]].text
        versions = {source["system_version"] for source in result["evidence"]}
        assert versions == ({"legacy", "mod_v1"} if scenario.scope == "compare" else {scenario.scope})


def test_demo_fails_visibly_when_required_evidence_is_missing():
    assistant = DemoAssistant()
    assistant.chunks = []
    result = assistant.present(SCENARIOS[0])
    assert result["status"] == "error"
    assert result["evidence"] == []


def test_guided_demo_navigation_sources_and_no_live_initialization(monkeypatch):
    def forbidden():
        raise AssertionError("Guided demo must not initialize the live assistant")
    monkeypatch.setattr("knowledge_assistant.core.KnowledgeAssistant", forbidden)
    app = AppTest.from_file(APP)
    app.query_params["demo"] = "1"
    app.run()
    assert not app.exception
    assert "not live AI answers" in app.info[0].value
    assert any("&amp;demo=1" in item.value for item in app.markdown)
    for index in range(1, len(SCENARIOS)):
        next(button for button in app.button if button.label == "Next scenario").click().run()
        assert not app.exception
        assert app.selectbox[0].value == index
    next(button for button in app.button if button.label == "Restart demo").click().run()
    assert app.selectbox[0].value == 0
    assert not app.exception


def test_demo_live_handoff_preserves_question_and_scope(monkeypatch):
    calls = []
    def answer(question, scope):
        calls.append((question, scope))
        return {"status": "supported", "summary": "Live result", "evidence": []}
    fake = SimpleNamespace(chunks=DemoAssistant().chunks, provider_error="", answer_question=answer)
    monkeypatch.setattr("knowledge_assistant.core.KnowledgeAssistant", lambda: fake)
    app = AppTest.from_file(APP)
    app.query_params["demo"] = "1"
    app.run()
    app.selectbox[0].set_value(3).run()
    next(button for button in app.button if button.label == "Ask live model").click().run()
    assert not app.exception
    assert calls == [(SCENARIOS[3].question, SCENARIOS[3].scope)]
    app.run()
    assert len(calls) == 1
    assert app.toggle[0].value is False
