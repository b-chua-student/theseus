from _thread import LockType
from dataclasses import dataclass, field
from threading import Lock
from weakref import WeakValueDictionary

from domain.assistant.models.value_objects import DocumentRefId


@dataclass
class DocumentIndexingState:
    """Serialize commits and identify the current job for one document."""

    lock: LockType = field(default_factory=Lock)
    active_job: object | None = None


class IndexingState:
    """Share per-document state while any worker or removal handler holds it."""

    def __init__(self) -> None:
        """Keep idle documents out of the coordination table."""
        self._guard = Lock()
        self._documents: WeakValueDictionary[DocumentRefId, DocumentIndexingState] = (
            WeakValueDictionary()
        )

    def for_document(self, ref: DocumentRefId) -> DocumentIndexingState:
        """Return the same state for overlapping operations on this reference."""
        with self._guard:
            state = self._documents.get(ref)
            if state is None:
                state = DocumentIndexingState()
                self._documents[ref] = state
            return state
