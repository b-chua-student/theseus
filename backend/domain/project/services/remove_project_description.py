from domain.project.models.aggregates import Project
from domain.project.models.value_objects import ProjectId, ProjectName
from domain.project.infrastructure.ports.project_repository import ProjectRepository

class RemoveProjectDescriptionService:
    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str) -> None:
        valid_project_id = ProjectId.from_str(project_id)
        
        project = self._repository.get_project_by_id(valid_project_id)
        
        if project is not None:
            project.remove_description()
            self._repository.update_project(project)

