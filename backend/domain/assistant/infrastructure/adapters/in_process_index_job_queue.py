import logging
from collections import deque
from collections.abc import Callable

from domain.assistant.infrastructure.ports.index_job_queue import IndexJobQueue
from domain.assistant.models.value_objects import DocumentRefId

logger = logging.getLogger(__name__)


class InProcessIndexJobQueue(IndexJobQueue):
    """Synchronous in-process queue that runs the indexing worker immediately.

    In production this would be replaced with a proper task queue (e.g. Celery,
    RQ, or a cloud task service). For now, callers may register a worker via
    ``set_worker``. If no worker is registered the job is stored in an internal
    deque so it can be drained in tests.
    """

    def __init__(self) -> None:
        """Initialize an empty queue with no worker registered."""
        self._pending: deque[DocumentRefId] = deque()
        self._worker: Callable[[DocumentRefId], None] | None = None

    def set_worker(self, worker: Callable[[DocumentRefId], None]) -> None:
        """Register the worker for future indexing submissions."""
        self._worker = worker

    def enqueue_index(self, doc_ref_id: DocumentRefId) -> None:
        """Run the worker immediately if registered, or add the document to the pending queue."""
        if self._worker is not None:
            try:
                self._worker(doc_ref_id)
            except Exception:
                logger.exception("Index worker failed for doc_ref_id=%s", doc_ref_id)
        else:
            self._pending.append(doc_ref_id)
            logger.debug("Queued index job for doc_ref_id=%s (no worker registered)", doc_ref_id)

    @property
    def pending(self) -> list[DocumentRefId]:
        """Return a list of pending document reference IDs."""
        return list(self._pending)
