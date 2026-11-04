from abc import ABC, abstractmethod

from domain.revision_history.models.value_objects import Snapshot


class ManuscriptWriter(ABC):
    """Port for writing a revision history snapshot back as the manuscript's current content."""

    @abstractmethod
    def apply_snapshot(self, manuscript_id: str, snapshot: Snapshot) -> None:
        """Replace the manuscript's current content with the given snapshot."""
        ...
