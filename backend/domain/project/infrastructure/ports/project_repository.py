from abc import ABC, abstractmethod

from domain.project.models.aggregates import Project
from domain.project.models.value_objects import MemberId, ProjectId


class ProjectRepository(ABC):
    @abstractmethod
    def get_projects_owned_by_member_id(self, member_id: MemberId) -> list[Project]:
        pass

    @abstractmethod
    def add_project(self, project: Project) -> None:
        pass

    @abstractmethod
    def get_project_by_id(self, project_id: ProjectId) -> Project | None:
        pass
    
    @abstractmethod
    def update_project(self, new_project: Project) -> None:
        pass

    @abstractmethod
    def delete_project_by_id(self, project_id: ProjectId) -> None:
        pass
