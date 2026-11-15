from abc import ABC, abstractmethod
from uuid import UUID

from domain.manuscript.aggregates import Manuscript


class ManuscriptRepository(ABC):
    """Abstract repository for persisting and retrieving manuscripts."""

    @abstractmethod
    def save(self, manuscript: Manuscript) -> None:
        """Persist a manuscript, creating or updating it.

        Args:
            manuscript: The manuscript to save.
        """
        pass

    @abstractmethod
    def get_by_id(self, manuscript_id: UUID) -> Manuscript | None:
        """Retrieve a manuscript by its identifier.

        Args:
            manuscript_id: The unique identifier of the manuscript.

        Returns:
            The matching manuscript, or None if not found.
        """
        pass

    @abstractmethod
    def get_by_project_id(self, project_id: UUID) -> list[Manuscript]:
        """Retrieve all manuscripts belonging to a project.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            A list of manuscripts for the project, empty if none exist.
        """
        pass

    @abstractmethod
    def get_all(self) -> list[Manuscript]:
        """Retrieve all stored manuscripts.

        Returns:
            A list of all manuscripts, empty if none exist.
        """
        pass

    @abstractmethod
    def delete(self, manuscript_id: UUID) -> None:
        """Delete a manuscript by its identifier.

        Args:
            manuscript_id: The unique identifier of the manuscript.
        """
        pass

    @abstractmethod
    def exists(self, manuscript_id: UUID) -> bool:
        """Check whether a manuscript exists.

        Args:
            manuscript_id: The unique identifier of the manuscript.

        Returns:
            True if the manuscript exists, otherwise False.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all manuscripts from the repository."""
        pass
