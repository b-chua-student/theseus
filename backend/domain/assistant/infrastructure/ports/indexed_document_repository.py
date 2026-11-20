from abc import ABC, abstractmethod

from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId, ProjectId


class IndexedDocumentRepository(ABC):
    """Port for persisting and retrieving IndexedDocument aggregates."""

    @abstractmethod
    def add(self, document: IndexedDocument) -> None:
        """Store a newly created document."""

    @abstractmethod
    def save(self, document: IndexedDocument) -> None:
        """Persist changes to an existing document."""

    @abstractmethod
    def get_by_doc_ref_id(self, doc_ref_id: DocumentRefId) -> IndexedDocument | None:
        """Return the document for ``doc_ref_id``, or None if it is not indexed."""

    @abstractmethod
    def list_by_project(self, project_id: ProjectId) -> list[IndexedDocument]:
        """Return all documents belonging to the given project."""
