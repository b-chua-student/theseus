from abc import ABC, abstractmethod
from collections.abc import Callable

from domain.assistant.models.value_objects import DocumentRefId


class IndexJobQueue(ABC):
    """Port for scheduling documents to be indexed asynchronously."""

    @abstractmethod
    def enqueue_index(self, doc_ref_id: DocumentRefId) -> None:
        """Schedule the document identified by ``doc_ref_id`` for indexing."""

    @abstractmethod
    def set_worker(self, worker: Callable[[DocumentRefId], None]) -> None:
        """Register the callable that processes each enqueued document."""
