import logging

from domain.src_lib.models.events import SourceUpdated

from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import (
    DocumentRefId,
    IndexedDocumentTitle,
    IndexStatus,
    ProjectId,
)

logger = logging.getLogger(__name__)


class OnSourceUpdated:
    """Reindex a text source after it is edited.

    Marks the existing IndexedDocument stale (so it is not searchable on old content)
    and enqueues a new indexing job. The vector store upsert replaces old chunks.
    """

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        queue: IndexJobQueue,
        provider: SourceContentProvider | None = None,
    ) -> None:
        """Configure the dependencies used to reindex updated sources."""
        self._repository = repository
        self._queue = queue
        self._provider = provider

    def __call__(self, event: SourceUpdated) -> None:
        """Flag the document for reindex and enqueue it."""
        doc_ref_id = DocumentRefId(event.source_id.value)
        title = self._title(doc_ref_id)
        indexed = self._repository.get_by_doc_ref_id(doc_ref_id)

        if indexed is None:
            indexed = IndexedDocument.create(
                title=IndexedDocumentTitle(title or f"Text source {event.source_id.value}"),
                doc_ref_id=doc_ref_id,
                project_id=ProjectId(event.project_id),
            )
            self._repository.add(indexed)
        else:
            if title:
                indexed.rename(IndexedDocumentTitle(title))
            if indexed.status is not IndexStatus.INDEXING:
                # An in-flight job may have read old content; the new enqueue below
                # re-runs the pipeline once it finishes.
                indexed.mark_stale()
            self._repository.save(indexed)

        self._queue.enqueue_index(doc_ref_id)

    def _title(self, doc_ref_id: DocumentRefId) -> str | None:
        return self._provider.get_title(doc_ref_id) if self._provider is not None else None
