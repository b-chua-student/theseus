from uuid import UUID

from repositories.project.project_repository import ProjectRepository


class DeleteProjectService:
    """Application service for deleting a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist projects.
        """
        self._repository = repository

    def execute(self, project_id: UUID) -> None:
        """Delete a project by its identifier.

        Args:
            project_id: Unique identifier of the project to delete.

        Raises:
            ValueError: If the project does not exist.
        """
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ValueError(f"Project with ID {project_id} not found.")

        self._repository.delete(project_id)
