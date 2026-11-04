from abc import ABC, abstractmethod

from domain.assistant.models.value_objects import (
    Chunk,
    DocumentRefId,
    Embedding,
    RetrievedChunk,
)


class VectorStore(ABC):
    """Port for storing chunk embeddings and running similarity search over them."""

    @abstractmethod
    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        """Replace all vectors for ``doc_ref_id``; ``chunks`` supply the text returned by query."""

    @abstractmethod
    def delete(self, doc_ref_id: DocumentRefId) -> None:
        """Remove all vectors stored for ``doc_ref_id``."""

    @abstractmethod
    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top ``k`` chunks nearest to ``query_embedding``, best first.

        If ``doc_ref_ids`` is given, restrict the search to those documents.
        """
