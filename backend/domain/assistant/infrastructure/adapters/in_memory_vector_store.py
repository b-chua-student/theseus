"""In-memory vector store.

Holds embeddings in a process-local dictionary keyed by DocumentRefId. Suitable
for the default pipeline and tests. Production deployments should swap in
``ChromaVectorStore`` via the container.
"""

import math

from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.value_objects import (
    Chunk,
    DocumentRefId,
    Embedding,
    RetrievedChunk,
)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class InMemoryVectorStore(VectorStore):
    """Dict-backed vector store."""

    def __init__(self) -> None:
        self._store: dict[DocumentRefId, list[Embedding]] = {}
        self._chunks: dict[DocumentRefId, dict] = {}

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        self._store[doc_ref_id] = list(embeddings)
        self._chunks[doc_ref_id] = {c.id: c for c in chunks}

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        self._store.pop(doc_ref_id, None)
        self._chunks.pop(doc_ref_id, None)

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        if k <= 0:
            return []
        results: list[RetrievedChunk] = []
        for doc_ref_id, embeddings in self._store.items():
            if doc_ref_ids is not None and doc_ref_id not in doc_ref_ids:
                continue
            for emb in embeddings:
                chunk = self._chunks.get(doc_ref_id, {}).get(emb.chunk_id)
                if chunk is None:
                    continue
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        doc_ref_id=doc_ref_id,
                        text=chunk.text,
                        position=chunk.position,
                        location=chunk.location,
                        score=_cosine(query_embedding, emb.vector),
                    )
                )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    @property
    def store(self) -> dict[DocumentRefId, list[Embedding]]:
        return self._store
