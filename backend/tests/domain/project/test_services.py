"""Unit tests for project application services."""

import pytest

from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from domain.project.models.entities import Member
from domain.project.models.errors import NotAProjectMemberError
from domain.project.models.value_objects import DisplayName, Email, MemberId, ProjectId, Role
from domain.project.services.create_project import CreateProjectService
from domain.project.services.delete_project import DeleteProjectService
from domain.project.services.edit_project_description import EditProjectDescriptionService
from domain.project.services.get_project import GetProjectService
from domain.project.services.list_projects import ListProjectsService
from domain.project.services.remove_project_description import RemoveProjectDescriptionService
from domain.project.services.rename_project import RenameProjectService
from domain.project.services.transfer_project_ownership import TransferProjectOwnershipService


def test_create_get_and_list_projects() -> None:
    """Verify CreateProjectService persists a project retrievable by Get and List services."""
    repo = InMemoryProjectRepository()
    owner_id = str(MemberId.new().value)

    CreateProjectService(repo).execute(
        project_name="Thesis Tracker",
        owner_id=owner_id,
        owner_name="Harvey",
        owner_email="harvey@example.com",
    )

    listed = ListProjectsService(repo).execute(owner_id=owner_id)
    assert len(listed) == 1
    assert listed[0].name.value == "Thesis Tracker"
    assert listed[0].owner.display_name.value == "Harvey"

    fetched = GetProjectService(repo).execute(str(listed[0].id.value))
    assert fetched is listed[0]
    assert GetProjectService(repo).execute(str(ProjectId.new().value)) is None


def test_rename_and_description_services() -> None:
    """Verify rename, edit description, and remove description services update stored state."""
    repo = InMemoryProjectRepository()
    owner_id = str(MemberId.new().value)
    CreateProjectService(repo).execute("Old Title", owner_id, "Harvey", "harvey@example.com")
    project = ListProjectsService(repo).execute(owner_id)[0]
    pid = str(project.id.value)

    RenameProjectService(repo).execute(pid, "New Title")
    EditProjectDescriptionService(repo).execute(pid, "Detailed scope")

    updated = GetProjectService(repo).execute(pid)
    assert updated is not None
    assert updated.name.value == "New Title"
    assert updated.description == "Detailed scope"

    RemoveProjectDescriptionService(repo).execute(pid)
    cleared = GetProjectService(repo).execute(pid)
    assert cleared is not None
    assert cleared.description is None


def test_services_ignore_missing_project_safely() -> None:
    """Verify mutation services act as safe no-ops when the project ID does not exist."""
    repo = InMemoryProjectRepository()
    missing_id = str(ProjectId.new().value)
    new_owner_id = str(MemberId.new().value)

    RenameProjectService(repo).execute(missing_id, "Ignored")
    EditProjectDescriptionService(repo).execute(missing_id, "Ignored")
    RemoveProjectDescriptionService(repo).execute(missing_id)
    TransferProjectOwnershipService(repo).execute(missing_id, new_owner_id)
    DeleteProjectService(repo).execute(missing_id)

    assert GetProjectService(repo).execute(missing_id) is None


def test_transfer_ownership_and_delete_services() -> None:
    """Verify ownership transfer and deletion through their respective application services."""
    repo = InMemoryProjectRepository()
    owner_id = str(MemberId.new().value)
    CreateProjectService(repo).execute("Capstone", owner_id, "Harvey", "harvey@example.com")
    project = ListProjectsService(repo).execute(owner_id)[0]
    pid = str(project.id.value)

    new_owner = Member.join(DisplayName("Bernard"), Email("bernard@example.com"), Role.EDITOR)
    project.add_member(new_owner)
    repo.update_project(project)

    with pytest.raises(NotAProjectMemberError):
        TransferProjectOwnershipService(repo).execute(pid, str(MemberId.new().value))

    TransferProjectOwnershipService(repo).execute(pid, str(new_owner.id.value))
    transferred = GetProjectService(repo).execute(pid)
    assert transferred is not None
    assert transferred.owner.id == new_owner.id

    DeleteProjectService(repo).execute(pid)
    assert GetProjectService(repo).execute(pid) is None
