import logging

from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import DocumentRefId, IndexedDocumentTitle, ProjectId
from domain.manuscript.models.events import ManuscriptSaved

logger = logging.getLogger(__name__)


class OnManuscriptSaved:
    """Create or re-queue an IndexedDocument when a manuscript is saved.

    Cross-context event handler: reacts to a ManuscriptSaved event from the Manuscript
    context so the assistant's working context stays current with the manuscript content.

    The manuscript_id is used as the DocumentRefId — each manuscript maps to one
    IndexedDocument in the assistant index, accumulating content across sections.
    """

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        queue: IndexJobQueue,
    ) -> None:
        self._repository = repository
        self._queue = queue

    def __call__(self, event: ManuscriptSaved) -> None:
        """Register the manuscript for indexing, or mark it stale if known, and enqueue indexing."""
        doc_ref_id = DocumentRefId(event.manuscript_id)

        indexed = self._repository.get_by_doc_ref_id(doc_ref_id)

        if indexed is None:
            # First section save for this manuscript — register it for indexing.
            indexed = IndexedDocument.create(
                title=IndexedDocumentTitle(f"Manuscript {event.manuscript_id}"),
                doc_ref_id=doc_ref_id,
                project_id=ProjectId(event.project_id),
            )
            self._repository.add(indexed)
            logger.debug(
                "OnManuscriptSaved: created IndexedDocument for manuscript_id=%s",
                event.manuscript_id,
            )
        else:
            # Manuscript already indexed — mark stale so the next indexing run
            # picks up the new section content.
            indexed.mark_stale()
            self._repository.save(indexed)
            logger.debug(
                "OnManuscriptSaved: marked IndexedDocument stale for manuscript_id=%s",
                event.manuscript_id,
            )

        self._queue.enqueue_index(doc_ref_id)
