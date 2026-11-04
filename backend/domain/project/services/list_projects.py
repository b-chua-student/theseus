from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.aggregates import Project
from domain.project.models.value_objects import MemberId


class ListProjectsService:
    """Use case: list the projects owned by a member."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, owner_id: str) -> list[Project]:
        """Return the projects owned by the member with the given ID."""
        valid_owner_id = MemberId.from_str(owner_id)
        return self._repository.get_projects_owned_by_member_id(valid_owner_id)
