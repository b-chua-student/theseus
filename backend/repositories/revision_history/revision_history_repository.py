from abc import ABC, abstractmethod
from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory


class RevisionHistoryRepository(ABC):
    @abstractmethod
    def save(self, history: RevisionHistory) -> None:
        """Persist a revision history."""
        raise NotImplementedError

    @abstractmethod
    def get_by_manuscript_id(
        self,
        manuscript_id: UUID,
    ) -> RevisionHistory | None:
        """Retrieve revision history by manuscript ID."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, manuscript_id: UUID) -> None:
        """Delete revision history for a manuscript."""
        raise NotImplementedError
