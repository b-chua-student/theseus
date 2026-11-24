import logging

from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.value_objects import IndexStatus

logger = logging.getLogger(__name__)


class ReindexDocumentsService:
    """Re-queue every indexed document so its vectors are rebuilt.

    Run this after changing the embedding model: searchable documents are marked stale and
    re-queued, so the ingestion worker replaces their vectors with ones from the current model.
    Failed or pending documents are re-queued too; documents being indexed are left alone.
    """

    def __init__(self, repository: IndexedDocumentRepository, queue: IndexJobQueue) -> None:
        """Set the document repository and the indexing queue."""
        self._repository = repository
        self._queue = queue

    def execute(self) -> int:
        """Re-queue the documents and return how many were queued."""
        queued = 0
        for document in self._repository.list_all():
            if document.status is IndexStatus.INDEXING:
                continue
            if document.is_searchable:
                document.mark_stale()
                self._repository.save(document)
            self._queue.enqueue_index(document.doc_ref_id)
            queued += 1
        logger.info("ReindexDocumentsService: re-queued %d documents", queued)
        return queued
