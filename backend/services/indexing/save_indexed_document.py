from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import Embedding
from repositories.indexing.indexed_document_repository import (
    IndexedDocumentRepository,
)


class SaveIndexedDocumentService:
    """Application service that persists an indexed document and its vectors."""

    def __init__(self, repository: IndexedDocumentRepository) -> None:
        self._repository = repository

    def execute(
        self,
        indexed_document: IndexedDocument,
        embeddings: list[Embedding] | None = None,
    ) -> None:
        self._repository.save(indexed_document, embeddings)
