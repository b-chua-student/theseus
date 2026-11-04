from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId, ProjectId


class InMemoryIndexedDocumentRepository(IndexedDocumentRepository):
    """Dict-backed IndexedDocumentRepository; contents are lost on restart."""

    def __init__(self) -> None:
        self._store: dict[str, IndexedDocument] = {}

    def add(self, document: IndexedDocument) -> None:
        key = str(document.doc_ref_id.value)
        self._store[key] = document

    def save(self, document: IndexedDocument) -> None:
        key = str(document.doc_ref_id.value)
        self._store[key] = document

    def get_by_doc_ref_id(self, doc_ref_id: DocumentRefId) -> IndexedDocument | None:
        return self._store.get(str(doc_ref_id.value))

    def list_by_project(self, project_id: ProjectId) -> list[IndexedDocument]:
        return [d for d in self._store.values() if d.project_id == project_id]
