from domain.project.models.aggregates import Project
from domain.project.models.value_objects import ProjectId
from domain.project.infrastructure.ports.project_repository import ProjectRepository

class GetProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str) -> Project | None:
        valid_project_id = ProjectId.from_str(project_id)

        return self._repository.get_project_by_id(valid_project_id)
