from abc import ABC, abstractmethod
from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory


class RevisionHistoryRepository(ABC):
    """Repository interface for manuscript revision histories."""

    @abstractmethod
    def save(self, revision_history: RevisionHistory) -> None:
        """Persist a revision history."""
        raise NotImplementedError

    @abstractmethod
    def get_by_manuscript_id(
        self,
        manuscript_id: UUID,
    ) -> RevisionHistory | None:
        """Retrieve a revision history by manuscript identifier."""
        raise NotImplementedError

    @abstractmethod
    def get_by_project_id(self, project_id: UUID) -> list[RevisionHistory]:
        """Retrieve revision histories belonging to a project."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[RevisionHistory]:
        """Retrieve all revision histories."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, manuscript_id: UUID) -> None:
        """Delete a revision history."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, manuscript_id: UUID) -> bool:
        """Check whether a revision history exists."""
        raise NotImplementedError
