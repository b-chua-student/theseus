from dataclasses import dataclass

from domain.project.infrastructure.ports.project_repository import ProjectRepository
from domain.project.services.create_project import CreateProjectService
from domain.project.services.delete_project import DeleteProjectService
from domain.project.services.edit_project_description import EditProjectDescriptionService
from domain.project.services.get_project import GetProjectService
from domain.project.services.list_projects import ListProjectsService
from domain.project.services.remove_project_description import RemoveProjectDescriptionService
from domain.project.services.rename_project import RenameProjectService
from domain.project.services.transfer_project_ownership import TransferProjectOwnershipService


@dataclass(frozen=True)
class ProjectModule:
    """Bundle of project use-case services sharing one repository."""

    create: CreateProjectService
    get: GetProjectService
    list: ListProjectsService
    delete: DeleteProjectService
    rename: RenameProjectService
    edit_description: EditProjectDescriptionService
    remove_description: RemoveProjectDescriptionService
    transfer_ownership: TransferProjectOwnershipService


def build_project_module(repo: ProjectRepository) -> ProjectModule:
    """Build a ProjectModule with every service wired to the given repository."""
    return ProjectModule(
        create=CreateProjectService(repository=repo),
        get=GetProjectService(repository=repo),
        list=ListProjectsService(repository=repo),
        delete=DeleteProjectService(repository=repo),
        rename=RenameProjectService(repository=repo),
        edit_description=EditProjectDescriptionService(repository=repo),
        remove_description=RemoveProjectDescriptionService(repository=repo),
        transfer_ownership=TransferProjectOwnershipService(repository=repo),
    )
