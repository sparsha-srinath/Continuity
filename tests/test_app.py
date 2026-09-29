import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from knowledge_assistant.llm_provider import ProviderConfig
from knowledge_assistant.workspace import AMI_QUESTION, AMI_UPDATE, LiveWorkspace

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def button(app, label):
    return next(b for b in app.button if b.label == label)


def field(app, kind, label):
    return next(w for w in getattr(app, kind) if w.label == label)


def test_workspace_pages_preview_publish_clear_and_restore():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    workspace = app.session_state['workspace']
    baseline = len(workspace.documents)
    button(app, 'Load a sample update +').click().run()
    assert not app.exception
    assert app.session_state['kb_tab'] == 'Add evidence'
    assert field(app, 'text_area', 'New source content').value == AMI_UPDATE
    button(app, 'Publish to knowledge base →').click().run()
    assert not app.exception
    assert len(workspace.documents) == baseline + 1
    assert workspace.revision == 2
    app.radio[0].set_value('Chunk explorer').run()
    app.slider[0].set_value(400).run()
    assert workspace.chunk_size == 1800
    button(app, 'Apply chunk size & rebuild index').click().run()
    assert not app.exception
    assert workspace.chunk_size == 400
    app.radio[0].set_value('Knowledge base').run()
    button(app, 'Clear knowledge base').click().run()
    assert not app.exception
    assert len(workspace.chunks) == 0
    button(app, 'Restore baseline corpus').click().run()
    assert not app.exception
    assert len(workspace.documents) == baseline
    assert workspace.chunk_size == 1800


def test_live_question_pin_update_and_source_snapshots(monkeypatch):
    original = LiveWorkspace.assistant
    def generator(query, context, scope):
        return json.dumps({'summary': 'Live test answer from selected evidence.', 'citations': [0], 'insufficient_evidence': False})
    monkeypatch.setattr(LiveWorkspace, 'assistant', lambda self: original(self, provider_config=ProviderConfig(), answer_generator=generator))
    app = AppTest.from_file(APP, default_timeout=30).run()
    button(app, 'Start the AMI workflow ↗').click().run()
    assert field(app, 'text_area', 'Your question').value == AMI_QUESTION
    button(app, 'Generate live answer ↗').click().run()
    assert not app.exception
    button(app, 'Pin as before').click().run()
    before = app.session_state['before_answer']
    assert before['revision'] == 1
    assert before['documents']
    button(app, 'Add new evidence +').click().run()
    button(app, 'Publish to knowledge base →').click().run()
    app.radio[0].set_value('Live Q&A').run()
    assert any('current KB is revision 02' in message.value for message in app.info)
    button(app, 'Generate live answer ↗').click().run()
    assert not app.exception
    assert len(app.session_state['answers']) == 2
    assert app.session_state['answers'][-1]['revision'] == 2
    assert app.session_state['before_answer']['revision'] == 1
    assert any('Full source at answer time' in item.value for item in app.markdown)
    assert not app.error


def test_model_failure_keeps_sources_visible(monkeypatch):
    original = LiveWorkspace.assistant
    monkeypatch.setattr(LiveWorkspace, 'assistant', lambda self: original(self, provider_config=ProviderConfig()))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Live Q&A').run()
    button(app, 'Generate live answer ↗').click().run()
    assert not app.exception
    assert app.error
    assert any('Retrieved sources' in item.value for item in app.markdown)
    assert any('Full source at answer time' in item.value for item in app.markdown)
