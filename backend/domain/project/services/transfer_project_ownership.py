from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.value_objects import MemberId, ProjectId


class TransferProjectOwnershipService:
    """Use case: transfer a project's ownership."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_id: str, new_owner_id: str) -> None:
        """Make the given member the owner of the project, if the project exists."""
        valid_project_id = ProjectId.from_str(project_id)
        valid_owner_id = MemberId.from_str(new_owner_id)

        project = self._repository.get_project_by_id(valid_project_id)

        if project is not None:
            project.transfer_ownership(valid_owner_id)
            self._repository.update_project(project)
