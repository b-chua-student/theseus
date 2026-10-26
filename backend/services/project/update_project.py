from uuid import UUID

from domain.project.aggregates import Project
from domain.project.value_objects import ProjectName
from repositories.project.project_repository import ProjectRepository


class UpdateProjectService:
    """Application service for renaming an existing project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist projects.
        """
        self._repository = repository

    def execute(self, project_id: UUID, name: str) -> Project:
        """Rename an existing project and persist the change.

        Args:
            project_id: Unique identifier of the project to update.
            name: New name for the project.

        Returns:
            The updated project aggregate.

        Raises:
            ValueError: If the project is not found or the name is invalid.
        """
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ValueError(f"Project with ID {project_id} not found.")

        project.rename(ProjectName(name))
        self._repository.save(project)
        return project
