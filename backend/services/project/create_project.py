from uuid import UUID, uuid4

from domain.project.aggregates import Project
from domain.project.value_objects import ProjectName
from repositories.project.project_repository import ProjectRepository


class CreateProjectService:
    """Application service for creating a new project."""

    def __init__(self, repository: ProjectRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist projects.
        """
        self._repository = repository

    def execute(self, owner_id: UUID, name: str) -> Project:
        """Create and persist a project.

        Args:
            owner_id: Identifier of the owning user.
            name: Name of the project.

        Returns:
            The newly created project.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        project = Project(
            id=uuid4(),
            owner_id=owner_id,
            name=ProjectName(name),
        )
        self._repository.save(project)
        return project
