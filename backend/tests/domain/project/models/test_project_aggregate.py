from collections.abc import Callable

import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.errors import IsCurrentOwnerError, NotAProjectMemberError
from domain.project.models.value_objects import (
    DisplayName,
    Email,
    ProjectName,
    Role,
)


@pytest.fixture
def member_factory() -> Callable[[str], Member]:
    def create_member(name: str = "Member") -> Member:
        email = f"{name.lower().replace(' ', '.')}@example.com"
        return Member.join(display_name=DisplayName(name), email=Email(email))

    return create_member


@pytest.fixture
def project_factory(member_factory: Callable[[str], Member]) -> Callable[..., Project]:
    def create_project(
        name: ProjectName | None = None,
        owner: Member | None = None,
    ) -> Project:
        return Project.create(
            name=name or ProjectName("My Project"),
            owner=owner or member_factory("Owner"),
        )

    return create_project


def test_add_member(member_factory, project_factory) -> None:
    project = project_factory()

    member = member_factory("Alice")
    project.add_member(member)

    assert member in project.members


def test_edit_role(project_factory, member_factory) -> None:
    project = project_factory()
    member = member_factory("Alice")
    project.add_member(member)

    project.edit_role(member, Role.EDITOR)

    changed_member = project.get_member_by_email("alice@example.com")
    assert changed_member is not None
    assert changed_member.id == member.id
    assert changed_member.role == Role.EDITOR


def test_transfer_ownership(member_factory, project_factory) -> None:
    owner = member_factory("Owner")
    project = project_factory(owner=owner)

    assert project.owner == owner

    new_owner = member_factory("Bob")
    project.add_member(new_owner)
    project.transfer_ownership(new_owner.id)

    assert project.owner == new_owner


def test_transfer_ownership_to_current_owner_fails(member_factory, project_factory) -> None:
    owner = member_factory("Owner")
    project = project_factory(owner=owner)

    with pytest.raises(IsCurrentOwnerError):
        project.transfer_ownership(owner.id)


def test_transfer_ownership_to_non_member_fails(member_factory, project_factory) -> None:
    project = project_factory()

    with pytest.raises(NotAProjectMemberError):
        project.transfer_ownership(member_factory("Stranger").id)
