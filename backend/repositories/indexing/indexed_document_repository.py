from abc import ABC, abstractmethod

from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import Embedding


class IndexedDocumentRepository(ABC):
    """Repository interface for indexed documents."""

    @abstractmethod
    def save(
        self,
        indexed_document: IndexedDocument,
        embeddings: list[Embedding] | None = None,
    ) -> None:
        """Persist an indexed document and, optionally, its chunk embeddings."""
