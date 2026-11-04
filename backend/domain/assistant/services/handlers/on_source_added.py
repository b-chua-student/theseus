from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId, IndexedDocumentTitle, ProjectId
from domain.src_lib.models.events import SourceAdded


class OnSourceAdded:
    """Create or re-flag an IndexedDocument when a source is added, then enqueue indexing.

    Cross-context event handler: reacts to a SourceAdded event from the Source Library
    context and updates the corresponding IndexedDocument in the Assistant context.
    """

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        queue: IndexJobQueue,
        provider: SourceContentProvider,
    ) -> None:
        self._repository = repository
        self._queue = queue
        self._provider = provider

    def __call__(self, event: SourceAdded) -> None:
        """Create the IndexedDocument if new (or mark a searchable one stale), then enqueue it."""
        # SourceAdded carries: source_id (SourceId), project_id (UUID), file_ref (str).
        # DocumentRefId is the assistant context's stable reference to the source file.
        doc_ref_id = DocumentRefId(event.source_id.value)

        indexed = self._repository.get_by_doc_ref_id(doc_ref_id)

        if indexed is None:
            # First time we see this source — create a pending IndexedDocument.
            # Use file_ref as a placeholder title until proper metadata is propagated.
            indexed = IndexedDocument.create(
                title=IndexedDocumentTitle(event.file_ref),
                doc_ref_id=doc_ref_id,
                project_id=ProjectId(event.project_id),
            )
            self._repository.add(indexed)
        elif indexed.is_searchable:
            # Source was re-added or updated; mark the existing index stale so it
            # gets re-processed.
            indexed.mark_stale()
            self._repository.save(indexed)

        self._queue.enqueue_index(doc_ref_id)
