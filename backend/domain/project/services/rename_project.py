from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.value_objects import ProjectId, ProjectName


class RenameProjectService:
    """Use case: rename a project."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str, new_name: str) -> None:
        """Rename the project with the given ID, if it exists."""
        valid_project_id = ProjectId.from_str(project_id)
        valid_project_name = ProjectName(new_name)

        project = self._repository.get_project_by_id(valid_project_id)

        if project is not None:
            project.rename(valid_project_name)
            self._repository.update_project(project)
