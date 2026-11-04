import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, ProjectName
from domain.project.services.transfer_project_ownership import TransferProjectOwnershipService


@pytest.fixture
def service(repository):
    return TransferProjectOwnershipService(repository)


def test_transfer_ownership_persists(repository, service) -> None:
    project = Project.create(
        name=ProjectName("Test Project"),
        owner=Member.join(display_name=DisplayName("Test User"), email=Email("test@example.com")),
    )

    repository.add_project(project)

    assert repository.get_project_by_id(project.id) is not None

    new_owner = Member.join(display_name=DisplayName("New User"), email=Email("new@email.com"))

    project.add_member(new_owner)
    project.transfer_ownership(new_owner.id)

    repository.update_project(project)

    retrieved = repository.get_project_by_id(project.id)

    assert retrieved is not None
    assert retrieved.owner is new_owner
