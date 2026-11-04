from abc import ABC, abstractmethod

from domain.assistant.models.value_objects import DocumentRefId


class SourceContentProvider(ABC):
    """Retrieves the raw text content of a source document by its reference ID."""

    @abstractmethod
    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        """Return the raw text of the source identified by ``doc_ref_id``."""
