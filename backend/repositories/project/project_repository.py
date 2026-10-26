from abc import ABC, abstractmethod
from uuid import UUID

from domain.project.aggregates import Project


class ProjectRepository(ABC):
    """Abstract repository for persisting and retrieving projects."""

    @abstractmethod
    def save(self, project: Project) -> None:
        """Persist a project, creating or updating it.

        Args:
            project: The project to save.
        """

    @abstractmethod
    def get_by_id(self, project_id: UUID) -> Project | None:
        """Retrieve a project by its identifier.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The matching project, or None if not found.
        """

    @abstractmethod
    def get_by_owner_id(self, owner_id: UUID) -> list[Project]:
        """Retrieve all projects owned by a user.

        Args:
            owner_id: The unique identifier of the owning user.

        Returns:
            A list of projects, empty if none exist.
        """

    @abstractmethod
    def delete(self, project_id: UUID) -> None:
        """Delete a project by its identifier.

        Args:
            project_id: The unique identifier of the project.
        """
