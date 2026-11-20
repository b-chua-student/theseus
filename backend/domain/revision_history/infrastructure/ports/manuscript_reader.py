from abc import ABC, abstractmethod

from domain.revision_history.models.value_objects import Snapshot


class ManuscriptReader(ABC):
    """Port for reading a manuscript's current content as a revision history snapshot."""

    @abstractmethod
    def get_snapshot(self, manuscript_id: str) -> Snapshot | None:
        """Return the manuscript's current snapshot, or None if it doesn't exist."""
        ...
