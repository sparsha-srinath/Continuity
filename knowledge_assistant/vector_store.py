import hashlib
from typing import Sequence

import chromadb


class DeterministicEmbeddingFunction:
    """Hashed lexical vectors, not a trained semantic embedding model."""

    def name(self):
        return "deterministic-embedding"

    def is_legacy(self):
        return False

    def _vectorize_text(self, text: str):
        from .retrieval import terms

        vector = [0.0] * 384
        for token in terms(text or ""):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest, "big") % len(vector)
            vector[bucket] += 1.0

        norm = sum(value * value for value in vector) ** 0.5
        if norm == 0:
            norm = 1.0
        return [value / norm for value in vector]

    def embed_documents(self, input: Sequence[str]):
        return [self._vectorize_text(text) for text in input]

    def embed_query(self, input: str):
        return self._vectorize_text(input)

    def __call__(self, input: Sequence[str]):
        if isinstance(input, str):
            return self.embed_query(input)
        return self.embed_documents(input)


class ChromaKnowledgeStore:
    def __init__(self, persist_directory: str = ".knowledge_store", *, client=None,
                 collection_name: str = "blpts_passages_v3"):
        self.client = client if client is not None else chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = DeterministicEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            # The collection name is versioned because changing embedding
            # dimensions is incompatible with an already-persisted Chroma index.
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_chunks(self, chunks):
        if not chunks:
            return

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for chunk in chunks:
            documents.append(chunk.text)
            metadatas.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "source_file": chunk.source_file,
                    "section_title": chunk.section_title,
                    "category": chunk.category,
                    "access": chunk.access,
                    "source_type": chunk.source_type,
                    "entity": chunk.entity,
                    "author": chunk.author,
                    "author_role_at_time": chunk.author_role_at_time,
                    "date": chunk.date,
                    "employment_status": chunk.employment_status,
                    "confidence_score": float(chunk.confidence_score),
                    "system_version": chunk.system_version,
                    "supersedes": chunk.supersedes or "",
                    "effective_from": chunk.effective_from or chunk.date,
                    "effective_to": chunk.effective_to or "",
                    "revision_of": chunk.revision_of or "",
                    "revision_number": int(chunk.revision_number),
                    "changed_by": chunk.changed_by or chunk.author,
                    "chunk_strategy": chunk.chunk_strategy,
                    "language": chunk.language,
                    "symbol_name": chunk.symbol_name,
                    "symbol_kind": chunk.symbol_kind,
                    "heading": chunk.heading,
                    "line_start": chunk.line_start,
                    "line_end": chunk.line_end,
                }
            )
            ids.append(chunk.chunk_id)
            embeddings.append(self.embedding_fn.embed_query(chunk.text))

        # Repository imports can exceed Chroma's per-request batch limit.
        batch_size = min(1000, self.client.get_max_batch_size())
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            self.collection.upsert(documents=documents[start:end], metadatas=metadatas[start:end],
                                   ids=ids[start:end], embeddings=embeddings[start:end])

    def query(self, query: str, top_k: int = 5, system_version: str | None = None):
        if top_k <= 0 or self.collection.count() == 0:
            return {"ids": [[]], "distances": [[]]}
        query_embedding = self.embedding_fn.embed_query(query)
        where = {"system_version": system_version} if system_version in {"legacy", "mod_v1"} else None
        return self.collection.query(query_embeddings=[query_embedding], n_results=top_k, where=where)
