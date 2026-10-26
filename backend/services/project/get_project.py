from uuid import UUID

from domain.project.aggregates import Project
from repositories.project.project_repository import ProjectRepository


class GetProjectService:
    """Application service for retrieving a single project by ID."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to retrieve projects.
        """
        self._repository = repository

    def execute(self, project_id: UUID) -> Project:
        """Fetch a project by its identifier.

        Args:
            project_id: Unique identifier of the project.

        Returns:
            The matching project.

        Raises:
            ValueError: If the project does not exist.
        """
        project = self._repository.get_by_id(project_id)
        if project is None:
            raise ValueError(f"Project with ID {project_id} not found.")
        return project
