from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.value_objects import ProjectId


class DeleteProjectService:
    """Use case: delete a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str) -> None:
        """Delete the project with the given ID."""
        valid_project_id = ProjectId.from_str(project_id)

        self._repository.delete_project_by_id(valid_project_id)
