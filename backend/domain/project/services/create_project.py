from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, MemberId, ProjectName, Role


class CreateProjectService:
    """Use case: create a project owned by a given user."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(self, project_name: str, owner_id: str, owner_name: str, owner_email: str) -> None:
        """Validate the inputs and store a new project."""
        valid_project_name = ProjectName(project_name)
        valid_owner = Member(
            id=MemberId.from_str(owner_id),
            display_name=DisplayName(owner_name),
            email=Email(owner_email),
            role=Role.VIEWER,
        )

        project = Project.create(
            name=valid_project_name,
            owner=valid_owner,
        )

        self._repository.add_project(project)
