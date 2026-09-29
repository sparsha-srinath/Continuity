"""Session-isolated, editable evidence with real Chroma indexing and live answers."""

from dataclasses import replace
from datetime import datetime, timezone
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
        self._apply(self.baseline, self.chunk_size, "Loaded baseline corpus")

    def _apply(self, documents, chunk_size, action):
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
                               "documents": len(documents), "chunks": len(chunks)})
        if previous is not None:
            self._client.delete_collection(previous.collection.name)

    def upsert(self, title, text, version="legacy", source_type="doc", document_id=None):
        if not title.strip() or not text.strip():
            raise ValueError("A document needs both a title and non-empty content.")
        if len(text.encode("utf-8")) > 500_000:
            raise ValueError("Keep each demo document below 500 KB.")
        if version not in {"legacy", "mod_v1"}:
            raise ValueError("Choose a valid system version.")
        existing = next((d for d in self.documents if d.chunk_id == document_id), None)
        if document_id is not None and existing is None:
            raise ValueError("This document is no longer in the knowledge base.")
        document = replace(existing, section_title=title.strip(), text=text,
                           system_version=version, source_type=source_type) if existing else SourceChunk(
            chunk_id="LIVE-" + uuid4().hex[:12], source_file="Session upload: " + title.strip(),
            section_title=title.strip(), text=text, system_version=version,
            source_type=source_type, category="live-upload", access="internal",
            entity=title.strip(), author="Demo presenter", author_role_at_time="Contributor",
            date=datetime.now(timezone.utc).date().isoformat(), employment_status="active",
            confidence_score=0.75,
        )
        documents = [document if d.chunk_id == document_id else d for d in self.documents]
        if existing is None:
            documents.append(document)
        self._apply(documents, self.chunk_size, ("Updated " if existing else "Added ") + title.strip())
        return document.chunk_id

    def remove(self, document_id):
        document = next((d for d in self.documents if d.chunk_id == document_id), None)
        if document is None:
            raise ValueError("This document is no longer in the knowledge base.")
        self._apply([d for d in self.documents if d.chunk_id != document_id], self.chunk_size,
                    "Removed " + document.section_title)

    def rebuild(self, chunk_size):
        self._apply(self.documents, chunk_size, f"Rebuilt index · {chunk_size:,} characters per chunk")

    def reset(self, empty=False):
        self._apply([] if empty else self.baseline, 1800,
                    "Cleared knowledge base" if empty else "Restored baseline corpus")

    def assistant(self, **kwargs):
        return KnowledgeAssistant(chunks=self.chunks, store=self.store,
                                  metadata_store=self.metadata, index_chunks=False, **kwargs)

    def document_chunks(self, document_id, size=None):
        document = next(d for d in self.documents if d.chunk_id == document_id)
        return split_chunks([document], max_chars=size or self.chunk_size)
