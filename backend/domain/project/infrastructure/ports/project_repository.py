from abc import ABC, abstractmethod

from domain.project.models.aggregates import Project
from domain.project.models.value_objects import MemberId, ProjectId


class ProjectRepository(ABC):
    """Port for storing and retrieving Project aggregates."""

    @abstractmethod
    def get_projects_owned_by_member_id(self, member_id: MemberId) -> list[Project]:
        """Return all projects whose owner has the given member ID."""

    @abstractmethod
    def add_project(self, project: Project) -> None:
        """Persist a new project."""

    @abstractmethod
    def get_project_by_id(self, project_id: ProjectId) -> Project | None:
        """Return the project with the given ID, or None if it does not exist."""

    @abstractmethod
    def update_project(self, new_project: Project) -> None:
        """Replace the stored project having the same ID as new_project."""

    @abstractmethod
    def delete_project_by_id(self, project_id: ProjectId) -> None:
        """Remove the project with the given ID, if present."""
