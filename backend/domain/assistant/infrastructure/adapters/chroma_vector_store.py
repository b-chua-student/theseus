"""ChromaDB-backed vector store adapter.

Embeddings are supplied by the application (the collection is created without
a Chroma embedding function), so query embeddings must come from the same model
and dimensionality as the ingested chunks. Distance is cosine; the returned
``score`` is ``1 - distance`` (higher is more similar).
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

import chromadb
from chromadb.api import ClientAPI

from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    Embedding,
    RetrievedChunk,
)

_DOC_KEY = "doc_ref_id"


class ChromaVectorStore(VectorStore):
    """VectorStore implementation on top of a single Chroma collection."""

    def __init__(
        self,
        client: ClientAPI | None = None,
        collection_name: str = "theseus_chunks",
        persist_path: str | None = None,
    ) -> None:
        """Create the adapter.

        Args:
            client: An existing Chroma client. Takes precedence over ``persist_path``.
            collection_name: Name of the collection holding all chunks.
            persist_path: If set (and no client given), use a persistent local client
                at this path; otherwise an ephemeral in-process client is used.
        """
        if client is None:
            client = (
                chromadb.PersistentClient(path=persist_path)
                if persist_path
                else chromadb.EphemeralClient()
            )
        self._collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        """Replace all stored vectors for ``doc_ref_id`` with the given embeddings."""
        chunk_by_id = {c.id: c for c in chunks}
        missing = [e.chunk_id for e in embeddings if e.chunk_id not in chunk_by_id]
        if missing:
            raise ValueError(f"No chunk supplied for embedding(s): {missing}")

        # Replace semantics: drop stale chunks from a previous indexing run.
        self.delete(doc_ref_id)
        if not embeddings:
            return

        ordered = [chunk_by_id[e.chunk_id] for e in embeddings]
        vectors: list[Sequence[float] | Sequence[int]] = [e.vector for e in embeddings]
        self._collection.upsert(
            ids=[str(c.id.value) for c in ordered],
            embeddings=vectors,
            documents=[c.text for c in ordered],
            metadatas=[
                {
                    _DOC_KEY: str(doc_ref_id.value),
                    "position": c.position,
                    "location": c.location,
                    "content_hash": c.content_hash,
                }
                for c in ordered
            ],
        )

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        """Remove every chunk belonging to ``doc_ref_id`` (no-op if none)."""
        self._collection.delete(where={_DOC_KEY: str(doc_ref_id.value)})

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the ``k`` nearest chunks to ``query_embedding``, best match first."""
        if k <= 0 or (doc_ref_ids is not None and not doc_ref_ids):
            return []
        total = self._collection.count()
        if total == 0:
            return []

        where: dict[str, Any] | None = None
        if doc_ref_ids is not None:
            where = {_DOC_KEY: {"$in": [str(d.value) for d in doc_ref_ids]}}

        query_vectors: list[Sequence[float] | Sequence[int]] = [query_embedding]
        res = self._collection.query(
            query_embeddings=query_vectors,
            n_results=min(k, total),
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        return [
            RetrievedChunk(
                chunk_id=ChunkId(UUID(cid)),
                doc_ref_id=DocumentRefId(UUID(str(meta[_DOC_KEY]))),
                text=text or "",
                position=str(meta.get("position", "")),
                location=str(meta.get("location", "")),
                score=1.0 - float(dist),
            )
            for cid, text, meta, dist in zip(ids, docs, metas, dists, strict=True)
        ]
