"""Session-isolated, editable evidence with real Chroma indexing and live answers."""

from dataclasses import replace
from hashlib import sha256
from datetime import date, datetime, timezone
from uuid import uuid4

import chromadb

from .core import KnowledgeAssistant
from .ingestion import build_seed_documents
from .models import SourceChunk
from .retrieval import split_chunks
from .vector_store import ChromaKnowledgeStore


AMI_QUESTION = "What are the exact AMI meter retry limits and backoff timings?"
AMI_UPDATE = """# AMI meter retry configuration — owner clarification

Synthetic demo update | Integration Operations | 2026-09-29

## Confirmed retry settings
The AMI meter upload integration retries a failed upload up to 4 times.
The delays before those retries are 5 seconds, 10 seconds, 20 seconds, and
40 seconds. After the fourth unsuccessful retry, the upload is moved to
the dead-letter queue and an operations alert is raised.

## Scope and provenance
These values describe the legacy AMI meter upload integration in this
synthetic demonstration. This note supplements MeterDataIntegration.md,
which describes exponential backoff without specific values. The earlier
email about missing durable documentation predates this clarification.
These settings do not describe BLPTS license renewals or inspections.

## Recovery
An operator reviews the dead-letter queue, fixes the underlying failure,
and replays the upload. Preserve the original upload identifier to avoid
duplicate meter readings. Alert ownership rests with Integration Operations.
"""


class SessionMetadata:
    def __init__(self):
        self.queries = []

    def record_query(self, query_text, result_status):
        self.queries.append({"question": query_text, "status": result_status})


class LiveWorkspace:
    """A browser session owns its documents, index, revisions, and query history.

    Rebuild into a new collection before swapping so a failed index leaves the
    previous revision usable. No original source file or persistent KB is edited.
    """

    def __init__(self, documents=None):
        self.baseline = list(build_seed_documents() if documents is None else documents)
        self.documents = []
        self.chunks = []
        self.chunk_size = 1800
        self.revision = 0
        self.events = []
        self.metadata = SessionMetadata()
        self.store = None
        self._client = chromadb.EphemeralClient()
        self._apply(self.baseline, self.chunk_size, "Loaded baseline corpus", changed_by="System")

    def _apply(self, documents, chunk_size, action, *, changed_by="System", effective_from=""):
        if not 200 <= chunk_size <= 3000:
            raise ValueError("Chunk size must be between 200 and 3000 characters.")
        chunks = split_chunks(documents, max_chars=chunk_size)
        collection_name = "live_demo_" + uuid4().hex
        store = ChromaKnowledgeStore(client=self._client, collection_name=collection_name)
        try:
            store.index_chunks(chunks)
        except Exception:
            self._client.delete_collection(collection_name)
            raise
        previous = self.store
        self.store = store
        self.documents = list(documents)
        self.chunks = chunks
        self.chunk_size = chunk_size
        self.revision += 1
        self.events.insert(0, {"revision": self.revision, "action": action,
                               "time": datetime.now().strftime("%H:%M:%S"),
                               "documents": len(documents), "chunks": len(chunks),
                               "changed_by": changed_by, "effective_from": effective_from})
        if previous is not None:
            self._client.delete_collection(previous.collection.name)

    def upsert(self, title, text, version="legacy", source_type="doc", document_id=None, *, effective_from=None):
        if not title.strip() or not text.strip():
            raise ValueError("A document needs both a title and non-empty content.")
        if len(text.encode("utf-8")) > 500_000:
            raise ValueError("Keep each demo document below 500 KB.")
        if version not in {"legacy", "mod_v1"}:
            raise ValueError("Choose a valid system version.")
        effective_date = effective_from or datetime.now(timezone.utc).date().isoformat()
        try:
            effective_date = date.fromisoformat(str(effective_date)).isoformat()
        except ValueError as error:
            raise ValueError("Effective date must use YYYY-MM-DD.") from error
        existing = next((d for d in self.documents if d.chunk_id == document_id), None)
        if document_id is not None and existing is None:
            raise ValueError("This document is no longer in the knowledge base.")
        if existing is not None and existing.effective_to is not None:
            raise ValueError("Historical sources cannot be edited. Update the current revision instead.")
        changed_at = datetime.now(timezone.utc).isoformat()
        changed_by = "Sparsha"
        document = SourceChunk(
            chunk_id="LIVE-" + uuid4().hex[:12], source_file=existing.source_file if existing else "Session upload: " + title.strip(),
            section_title=title.strip(), text=text, system_version=version,
            source_type=source_type, category=existing.category if existing else "live-upload",
            access=existing.access if existing else "internal", entity=existing.entity if existing else title.strip(),
            author=changed_by, author_role_at_time="Contributor",
            date=effective_date, employment_status="active", confidence_score=existing.confidence_score if existing else 0.75,
            supersedes=existing.chunk_id if existing else None,
            effective_from=effective_date,
            revision_of=(existing.revision_of or existing.chunk_id) if existing else None,
            revision_number=(existing.revision_number + 1) if existing else 1,
            changed_by=changed_by, changed_at=changed_at,
        )
        if existing is None:
            documents = list(self.documents) + [document]
        else:
            prior = replace(existing, effective_to=effective_date, employment_status="superseded")
            documents = [prior if d.chunk_id == existing.chunk_id else d for d in self.documents] + [document]
        self._apply(documents, self.chunk_size, ("Updated " if existing else "Added ") + title.strip(),
                    changed_by=changed_by, effective_from=effective_date)
        return document.chunk_id

    def source_history(self, document_id):
        document = next((d for d in self.documents if d.chunk_id == document_id), None)
        if document is None:
            raise ValueError("This document is no longer in the knowledge base.")
        root = document.revision_of or document.chunk_id
        lineage = [d for d in self.documents if (d.revision_of or d.chunk_id) == root]
        return sorted(lineage, key=lambda d: (d.revision_number, d.changed_at, d.chunk_id))

    def remove(self, document_id):
        document = next((d for d in self.documents if d.chunk_id == document_id), None)
        if document is None:
            raise ValueError("This document is no longer in the knowledge base.")
        if document.effective_to is not None:
            raise ValueError("Historical sources are retained as an audit record and cannot be removed.")
        self._apply([d for d in self.documents if d.chunk_id != document_id], self.chunk_size,
                    "Removed " + document.section_title, changed_by="Sparsha")

    def import_codebase(self, files, project, version="legacy"):
        from .codebase_import import MAX_FILE_BYTES, MAX_FILES, MAX_TOTAL_BYTES, path_issue

        project = project.strip()
        if not project or len(project) > 100:
            raise ValueError("Enter a codebase name of 1–100 characters.")
        if version not in {"legacy", "mod_v1"}:
            raise ValueError("Choose a valid system version.")
        if not files or len(files) > MAX_FILES:
            raise ValueError("Select between 1 and 500 source files.")
        if sum(len(f.text.encode("utf-8")) for f in files) > MAX_TOTAL_BYTES:
            raise ValueError("Keep expanded source below 10 MB per batch.")
        documents = {d.chunk_id: d for d in self.documents}
        for source in files:
            if path_issue(source.path) or not source.text.strip() or len(source.text.encode("utf-8")) > MAX_FILE_BYTES:
                raise ValueError(f"Unsupported source: {source.path}")
            identity = f"{len(project)}:{project}:{version}:{source.path}"
            chunk_id = "REPO-" + sha256(identity.encode("utf-8")).hexdigest()[:24]
            documents[chunk_id] = SourceChunk(
                chunk_id=chunk_id, source_file=f"Codebase {project}/{source.path}", section_title=source.path,
                text=source.text, system_version=version, source_type=source.source_type,
                category="codebase-import", access="internal", entity=project,
                author="Demo presenter", author_role_at_time="Contributor",
                date=datetime.now(timezone.utc).date().isoformat(), employment_status="active", confidence_score=0.75,
            )
        self._apply(list(documents.values()), self.chunk_size, f"Imported {len(files)} files from {project}",
                    changed_by="Sparsha")

    def rebuild(self, chunk_size):
        self._apply(self.documents, chunk_size, f"Rebuilt index · {chunk_size:,} characters per chunk",
                    changed_by="Sparsha")

    def reset(self, empty=False):
        self._apply([] if empty else self.baseline, 1800,
                    "Cleared knowledge base" if empty else "Restored baseline corpus", changed_by="Sparsha")

    def assistant(self, **kwargs):
        return KnowledgeAssistant(chunks=self.chunks, store=self.store,
                                  metadata_store=self.metadata, index_chunks=False, **kwargs)

    def document_chunks(self, document_id, size=None):
        document = next(d for d in self.documents if d.chunk_id == document_id)
        return split_chunks([document], max_chars=size or self.chunk_size)
