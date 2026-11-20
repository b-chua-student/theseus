from abc import ABC, abstractmethod

from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.value_objects import ManuscriptId


class RevisionHistoryRepository(ABC):
    """Port for persisting and retrieving a manuscript's revision history."""

    @abstractmethod
    def get_by_manuscript_id(self, manuscript_id: ManuscriptId) -> RevisionHistory | None:
        """Return the revision history for a manuscript, or None if none exists yet."""
        ...

    @abstractmethod
    def add(self, history: RevisionHistory) -> None:
        """Persist a newly created revision history."""
        ...

    @abstractmethod
    def save(self, history: RevisionHistory) -> None:
        """Persist changes to an existing revision history."""
        ...
