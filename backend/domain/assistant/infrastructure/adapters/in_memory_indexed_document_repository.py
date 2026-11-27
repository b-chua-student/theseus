from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId, ProjectId


class InMemoryIndexedDocumentRepository(IndexedDocumentRepository):
    """Dict-backed IndexedDocumentRepository; contents are lost on restart."""

    def __init__(self) -> None:
        """Initialize an empty in-memory indexed document store."""
        self._store: dict[str, IndexedDocument] = {}

    def add(self, document: IndexedDocument) -> None:
        """Store the indexed document under its document reference ID."""
        key = str(document.doc_ref_id.value)
        self._store[key] = document

    def save(self, document: IndexedDocument) -> None:
        """Store or replace the indexed document by reference ID."""
        key = str(document.doc_ref_id.value)
        self._store[key] = document

    def get_by_doc_ref_id(self, doc_ref_id: DocumentRefId) -> IndexedDocument | None:
        """Return the indexed document for the reference ID, if present."""
        return self._store.get(str(doc_ref_id.value))

    def list_by_project(self, project_id: ProjectId) -> list[IndexedDocument]:
        """List indexed documents for the given project."""
        return [d for d in self._store.values() if d.project_id == project_id]

    def list_all(self) -> list[IndexedDocument]:
        """List every indexed document."""
        return list(self._store.values())
