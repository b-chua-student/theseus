from domain.project.aggregates import Project
from repositories.project.project_repository import ProjectRepository


class GetAllProjectsService:
    """Application service for retrieving all projects."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to retrieve projects.
        """
        self._repository = repository

    def execute(self) -> list[Project]:
        """Retrieve all projects.

        Returns:
            A list of all projects, empty if none exist.
        """
        return self._repository.get_all()
