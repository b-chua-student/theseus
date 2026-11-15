import logging

from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.value_objects import DocumentRefId, IndexStatus
from domain.src_lib.models.events import SourceRemoved

logger = logging.getLogger(__name__)


class OnSourceRemoved:
    """Mark an IndexedDocument stale when its source is removed.

    Cross-context event handler: reacts to a SourceRemoved event from the Source Library
    context so the document is excluded from future search results.
    """

    def __init__(self, repository: IndexedDocumentRepository) -> None:
        self._repository = repository

    def __call__(self, event: SourceRemoved) -> None:
        """Mark the source's document stale, unless it is unknown or currently being indexed."""
        doc_ref_id = DocumentRefId(event.source_id.value)
        indexed = self._repository.get_by_doc_ref_id(doc_ref_id)

        if indexed is None:
            # Source was removed before it was ever indexed — nothing to do.
            logger.debug(
                "OnSourceRemoved: no IndexedDocument found for source_id=%s", event.source_id
            )
            return

        if indexed.status is IndexStatus.INDEXING:
            # Can't transition from INDEXING; the running job will call fail_indexing()
            # or complete_indexing() itself — skip.
            logger.debug(
                "OnSourceRemoved: document is currently being indexed, skipping for source_id=%s",
                event.source_id,
            )
            return

        # Mark the document pending (stale) so it is no longer treated as searchable.
        indexed.mark_stale()
        self._repository.save(indexed)
