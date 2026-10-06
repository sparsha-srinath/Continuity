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


def paste_sample_document(app):
    app.session_state['kb_tab'] = 'Add document'
    field(app, 'text_input', 'New document title').set_value('AMI retry configuration — owner clarification')
    field(app, 'text_area', 'New source content').set_value(AMI_UPDATE).run()


def test_overview_cards_open_applications_and_keep_the_workspace():
    app = AppTest.from_file(APP, default_timeout=30).run()
    workspace = app.session_state['workspace']
    for version in ('legacy', 'modernized'):
        app.button(key=f'overview-open-{version}').click().run()
        assert not app.exception
        assert app.session_state['overview_application'] == version
        button(app, 'Return to Continuity overview').click().run()
        assert app.session_state['workspace'] is workspace
    app.button(key='overview-open-Knowledge-base').click().run()
    assert app.session_state['page'] == 'Knowledge base'
    assert not app.exception


def test_workspace_pages_preview_publish_clear_and_restore():
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception
    workspace = app.session_state['workspace']
    baseline = len(workspace.documents)
    app.radio[0].set_value('Knowledge base').run()
    assert field(app, 'text_area', 'New source content').value == ''
    paste_sample_document(app)
    assert not app.exception
    assert app.session_state['kb_tab'] == 'Add document'
    assert field(app, 'text_area', 'New source content').value == AMI_UPDATE
    button(app, 'Publish to knowledge base').click().run()
    assert not app.exception
    assert len(workspace.documents) == baseline + 1
    assert workspace.revision == 2
    assert button(app, 'Published to knowledge base ✓').disabled
    assert any('Published: AMI retry configuration' in message.value for message in app.success)
    app.run()
    assert button(app, 'Published to knowledge base ✓').disabled
    assert any('Ready to use in Live Q&A.' in message.value for message in app.success)
    field(app, 'text_area', 'New source content').set_value(AMI_UPDATE + '\nAdditional evidence.').run()
    assert not button(app, 'Publish to knowledge base').disabled
    assert len(workspace.documents) == baseline + 1
    document_id = workspace.documents[-1].chunk_id
    field(app, 'selectbox', 'Source document').set_value(document_id).run()
    field(app, 'text_input', 'Document title').set_value('Updated AMI clarification').run()
    button(app, 'Save new revision & reindex').click().run()
    assert not app.exception
    assert len(workspace.documents) == baseline + 2
    assert any('New revision published.' in message.value for message in app.success)
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


def test_chunk_preview_updates_repeatedly_and_preserves_document_after_rebuild():
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Chunk explorer').run()
    workspace = app.session_state['workspace']
    document = next(d for d in workspace.documents if d.source_file.endswith('business_rules.py'))
    field(app, 'selectbox', 'Document to inspect').set_value(document.chunk_id).run()
    slider_id = app.slider[0].id
    for limit in (400, 700, 900):
        app.slider[0].set_value(limit).run()
        assert not app.exception
        assert field(app, 'selectbox', 'Document to inspect').value == document.chunk_id
        expected = workspace.document_chunks(document.chunk_id, limit)
        assert next(m for m in app.metric if m.label == 'Preview chunks').value == str(len(expected))
        assert app.code[0].value.strip() == expected[0].text.strip()
    button(app, 'Apply chunk size & rebuild index').click().run()
    assert field(app, 'selectbox', 'Document to inspect').value == document.chunk_id
    assert app.slider[0].id == slider_id
    for limit in (300, 1800, 2000):
        app.slider[0].set_value(limit).run()
        assert not app.exception
        assert field(app, 'selectbox', 'Document to inspect').value == document.chunk_id
        expected = workspace.document_chunks(document.chunk_id, limit)
        assert next(m for m in app.metric if m.label == 'Preview chunks').value == str(len(expected))
        assert app.code[0].value.strip() == expected[0].text.strip()
    assert any('boundaries are unchanged' in caption.value for caption in app.caption)
    app.radio[0].set_value('Knowledge base').run()
    button(app, 'Restore baseline corpus').click().run()
    app.radio[0].set_value('Chunk explorer').run()
    assert app.slider[0].value == 1800


def test_old_session_uses_current_sql_packer_without_losing_documents():
    class PreviousWorkspace(LiveWorkspace):
        def document_chunks(self, document_id, size=None):
            raise AssertionError('Retained workspace is using outdated methods')

    app = AppTest.from_file(APP, default_timeout=30).run()
    workspace = app.session_state['workspace']
    added_id = workspace.upsert('Session note', 'Keep this source through a code reload.')
    original_store = workspace.store
    events = list(workspace.events)
    workspace.__class__ = PreviousWorkspace
    app.radio[0].set_value('Chunk explorer').run()
    assert not app.exception
    assert type(workspace) is LiveWorkspace
    assert workspace.store is original_store
    assert workspace.events == events
    assert any(d.chunk_id == added_id for d in workspace.documents)
    document = next(d for d in workspace.documents
                    if d.source_file.endswith('seed_data.sql') and d.system_version == 'legacy')
    field(app, 'selectbox', 'Document to inspect').set_value(document.chunk_id).run()
    counts = []
    for limit in (500, 1800):
        app.slider[0].set_value(limit).run()
        assert not app.exception
        parts = workspace.document_chunks(document.chunk_id, limit)
        counts.append(len(parts))
        assert any(part.text.count(';') > 1 for part in parts)
    assert counts == [7, 2]


def test_publish_failure_preserves_draft_and_allows_retry(monkeypatch):
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Knowledge base').run()
    paste_sample_document(app)
    workspace = app.session_state['workspace']
    original = LiveWorkspace.upsert
    def fail(*args, **kwargs):
        raise RuntimeError('Index temporarily unavailable')
    monkeypatch.setattr(LiveWorkspace, 'upsert', fail)
    button(app, 'Publish to knowledge base').click().run()
    assert not app.exception
    assert workspace.revision == 1
    assert field(app, 'text_area', 'New source content').value == AMI_UPDATE
    assert any('Could not publish: Index temporarily unavailable' in message.value for message in app.error)
    assert not button(app, 'Publish to knowledge base').disabled
    monkeypatch.setattr(LiveWorkspace, 'upsert', original)
    button(app, 'Publish to knowledge base').click().run()
    assert not app.exception
    assert not app.error
    assert workspace.revision == 2
    assert button(app, 'Published to knowledge base ✓').disabled


def test_live_question_pin_update_and_source_snapshots(monkeypatch):
    original = LiveWorkspace.assistant
    def generator(query, context, scope):
        return json.dumps({'summary': 'Live test answer from selected evidence.', 'citations': [0], 'insufficient_evidence': False})
    monkeypatch.setattr(LiveWorkspace, 'assistant', lambda self: original(self, provider_config=ProviderConfig(), answer_generator=generator))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Live Q&A').run()
    assert field(app, 'text_area', 'Your question').value == ''
    button(app, 'Generate answer').click().run()
    assert not app.exception
    assert app.session_state['answers'] == []
    assert any('Enter a question' in message.value for message in app.info)
    field(app, 'text_area', 'Your question').set_value(AMI_QUESTION).run()
    button(app, 'Generate answer').click().run()
    assert not app.exception
    button(app, 'Pin baseline').click().run()
    before = app.session_state['before_answer']
    assert before['revision'] == 1
    assert before['documents']
    assert any('Baseline pinned.' in message.value for message in app.info)
    assert not any('**Before · revision' in item.value for item in app.markdown)
    assert len([b for b in app.button if b.label == 'Pin baseline']) == 1
    button(app, 'Add document').click().run()
    assert app.session_state['kb_tab'] == 'Add document'
    assert field(app, 'text_area', 'New source content').value == ''
    paste_sample_document(app)
    button(app, 'Publish to knowledge base').click().run()
    app.radio[0].set_value('Live Q&A').run()
    assert field(app, 'text_area', 'Your question').value == AMI_QUESTION
    assert any('current KB is revision 02' in message.value for message in app.info)
    button(app, 'Generate answer').click().run()
    assert not app.exception
    assert len(app.session_state['answers']) == 2
    assert app.session_state['answers'][-1]['revision'] == 2
    assert app.session_state['before_answer']['revision'] == 1
    assert field(app, 'selectbox', 'Answer history').value == 1
    assert sum('**Before · revision' in item.value for item in app.markdown) == 1
    assert sum('**After · revision' in item.value for item in app.markdown) == 1
    assert any('Full source at answer time' in item.value for item in app.markdown)
    button(app, 'Unpin comparison').click().run()
    assert not app.exception
    assert not any('**Before · revision' in item.value for item in app.markdown)
    assert len(app.session_state['answers']) == 2
    assert field(app, 'selectbox', 'Answer history').value == 1
    assert any('Full source at answer time' in item.value for item in app.markdown)
    assert not app.error


def test_model_failure_keeps_sources_visible(monkeypatch):
    original = LiveWorkspace.assistant
    monkeypatch.setattr(LiveWorkspace, 'assistant', lambda self: original(self, provider_config=ProviderConfig()))
    app = AppTest.from_file(APP, default_timeout=30).run()
    app.radio[0].set_value('Live Q&A').run()
    field(app, 'text_area', 'Your question').set_value(AMI_QUESTION).run()
    button(app, 'Generate answer').click().run()
    assert not app.exception
    assert app.error
    assert any('Retrieved sources' in item.value for item in app.markdown)
    assert any('Full source at answer time' in item.value for item in app.markdown)
