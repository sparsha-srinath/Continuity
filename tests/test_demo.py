from unittest.mock import Mock

import pytest

from knowledge_assistant.llm_provider import ProviderConfig
from knowledge_assistant.vector_store import ChromaKnowledgeStore
from knowledge_assistant.workspace import AMI_QUESTION, AMI_UPDATE, LiveWorkspace


def test_add_edit_remove_clear_restore_are_reflected_in_real_index():
    workspace = LiveWorkspace()
    original_ids = {c.chunk_id for c in workspace.chunks}
    doc_id = workspace.upsert('Zebra migration policy', 'Zebra migration launch requires four approvals. ' * 90)
    assert len(workspace.document_chunks(doc_id)) > 1
    assert any(c['chunk_id'].startswith(doc_id) for c in workspace.assistant(provider_config=ProviderConfig())._retrieve_candidates('zebra migration approvals', 'legacy'))
    revised_id = workspace.upsert('Zebra migration policy', 'Zebra migration now needs one approval.', document_id=doc_id,
                                  effective_from='2026-10-05')
    stored_ids = set(workspace.store.collection.get()['ids'])
    assert doc_id in stored_ids and revised_id in stored_ids
    assert workspace.source_history(revised_id)[0].effective_to == '2026-10-05'
    workspace.remove(revised_id)
    assert doc_id in set(workspace.store.collection.get()['ids'])
    workspace.reset()
    assert set(workspace.store.collection.get()['ids']) == original_ids
    workspace.reset(empty=True)
    generator = Mock()
    result = workspace.assistant(provider_config=ProviderConfig(), answer_generator=generator).answer_question(AMI_QUESTION, 'legacy')
    assert result['status'] == 'unsupported'
    generator.assert_not_called()
    assert workspace.store.collection.count() == 0
    workspace.reset()
    assert {c.chunk_id for c in workspace.chunks} == original_ids
    assert workspace.store.collection.count() == len(original_ids)


def test_sessions_are_isolated_and_preview_does_not_mutate_index():
    first, second = LiveWorkspace(), LiveWorkspace()
    second_ids = set(second.store.collection.get()['ids'])
    document = max(first.documents, key=lambda d: len(d.text))
    parts = first.document_chunks(document.chunk_id, 300)
    assert ''.join(c.text for c in parts) == document.text
    assert all(len(c.text) <= 300 for c in parts)
    assert first.chunk_size == 1800 and first.revision == 1
    first.rebuild(300)
    assert first.chunk_size == 300 and first.revision == 2
    assert all(len(c.text) <= 300 for c in first.chunks)
    first.reset(empty=True)
    assert set(second.store.collection.get()['ids']) == second_ids


def test_new_evidence_reaches_live_generator_and_reset_removes_it():
    workspace = LiveWorkspace()
    seen = []
    def generate(question, context, scope):
        import json
        seen.append(context)
        return json.dumps({'summary': 'Test response from supplied evidence.', 'citations': [0], 'insufficient_evidence': False})
    workspace.assistant(provider_config=ProviderConfig(), answer_generator=generate).answer_question(AMI_QUESTION, 'legacy')
    assert not any('5 seconds, 10 seconds' in c['text'] for c in seen[-1])
    new_id = workspace.upsert('AMI retry configuration', AMI_UPDATE)
    result = workspace.assistant(provider_config=ProviderConfig(), answer_generator=generate).answer_question(AMI_QUESTION, 'legacy')
    assert result['generation_method'] == 'model'
    assert any(c['chunk_id'] == new_id and '5 seconds, 10 seconds' in c['text'] for c in seen[-1])
    workspace.reset()
    workspace.assistant(provider_config=ProviderConfig(), answer_generator=generate).answer_question(AMI_QUESTION, 'legacy')
    assert not any(c['chunk_id'] == new_id for c in seen[-1])


def test_failed_rebuild_preserves_previous_revision(monkeypatch):
    workspace = LiveWorkspace()
    old_store = workspace.store
    old_ids = set(old_store.collection.get()['ids'])
    monkeypatch.setattr(ChromaKnowledgeStore, 'index_chunks', Mock(side_effect=RuntimeError('Index unavailable')))
    with pytest.raises(RuntimeError, match='Index unavailable'):
        workspace.upsert('New document', 'An example source.')
    assert workspace.store is old_store
    assert workspace.revision == 1
    assert set(workspace.store.collection.get()['ids']) == old_ids


@pytest.mark.parametrize('title,text', [('', 'valid'), ('valid', ' '), ('valid', 'x' * 500_001)],
                         ids=['empty-title', 'empty-content', 'oversize'])
def test_invalid_sources_do_not_change_revision(title, text):
    workspace = LiveWorkspace(documents=[])
    with pytest.raises(ValueError):
        workspace.upsert(title, text)
    assert workspace.revision == 1


def test_source_revisions_keep_history_and_retrieval_uses_current_guidance():
    workspace = LiveWorkspace(documents=[])
    first = workspace.upsert('AMI operations', 'Retry a failed upload twice.', effective_from='2026-01-01')
    current = workspace.upsert('AMI operations', 'Retry a failed upload four times.', document_id=first,
                               effective_from='2026-02-01')
    history = workspace.source_history(current)
    assert [item.revision_number for item in history] == [1, 2]
    assert history[0].effective_to == '2026-02-01'
    assert history[1].supersedes == first
    candidates = workspace.assistant()._retrieve_candidates('retry failed upload', 'legacy')
    assert {item['chunk_id'] for item in candidates} == {current}


def test_revision_events_record_the_actor_and_effective_date():
    workspace = LiveWorkspace(documents=[])
    workspace.upsert('AMI operations', 'Retry a failed upload twice.', effective_from='2026-01-01')
    assert workspace.events[0]['changed_by'] == 'Sparsha'
    assert workspace.events[0]['effective_from'] == '2026-01-01'
    workspace.reset()
    assert workspace.events[0]['changed_by'] == 'Sparsha'
