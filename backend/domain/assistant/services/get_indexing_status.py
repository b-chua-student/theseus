from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId


class GetIndexingStatusService:
    """Looks up the indexing status of a manuscript's IndexedDocument.

    The manuscript's doc_ref_id is its own id (see OnManuscriptSaved), so a
    manuscript maps to at most one IndexedDocument. Returns None when the
    manuscript has never been saved (and so was never queued for indexing).
    """

    def __init__(self, repository: IndexedDocumentRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str) -> IndexedDocument | None:
        """Return the IndexedDocument for ``manuscript_id``, or None if never indexed."""
        return self._repository.get_by_doc_ref_id(DocumentRefId.from_str(manuscript_id))
