"""Unit tests for project domain models, entities, value objects, and errors."""

from uuid import UUID

import pytest

from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.errors import (
    InvalidDisplayNameError,
    InvalidEmailError,
    InvalidProjectNameError,
    IsCurrentOwnerError,
    NotAProjectMemberError,
)
from domain.project.models.value_objects import (
    DisplayName,
    Email,
    MemberId,
    ProjectId,
    ProjectName,
    ProjectSettings,
    Role,
)


def test_project_id_generation_and_parsing() -> None:
    """Verify ProjectId generates valid UUIDs and round-trips through strings."""
    generated = ProjectId.new()
    parsed = ProjectId.from_str(str(generated.value))

    assert isinstance(generated.value, UUID)
    assert parsed == generated


def test_member_id_generation_and_parsing() -> None:
    """Verify MemberId generates valid UUIDs and round-trips through strings."""
    generated = MemberId.new()
    parsed = MemberId.from_str(str(generated.value))

    assert isinstance(generated.value, UUID)
    assert parsed == generated


def test_project_name_trims_whitespace_and_rejects_invalid_values() -> None:
    """Verify ProjectName strips surrounding whitespace and enforces length rules."""
    name = ProjectName("  Theseus Core  ")
    assert name.value == "Theseus Core"

    with pytest.raises(InvalidProjectNameError):
        ProjectName("   ")

    with pytest.raises(InvalidProjectNameError):
        ProjectName("a" * 257)


def test_display_name_trims_whitespace_and_rejects_invalid_values() -> None:
    """Verify DisplayName strips whitespace and enforces the 50-character limit."""
    display_name = DisplayName("  Ada Lovelace  ")
    assert display_name.value == "Ada Lovelace"

    with pytest.raises(InvalidDisplayNameError):
        DisplayName("   ")

    with pytest.raises(InvalidDisplayNameError):
        DisplayName("a" * 51)


def test_email_normalizes_and_rejects_invalid_addresses() -> None:
    """Verify Email normalizes valid addresses and raises InvalidEmailError otherwise."""
    email = Email("user@EXAMPLE.COM")
    assert email.value == "user@example.com"
    assert str(email) == "user@example.com"

    with pytest.raises(InvalidEmailError):
        Email("not-an-email")


def test_project_settings_default_language() -> None:
    """Verify ProjectSettings defaults to English unless overridden."""
    assert ProjectSettings.create_default().language == "en"
    assert ProjectSettings.create_default("tl").language == "tl"


def test_member_join_and_role_update() -> None:
    """Verify Member.join defaults to VIEWER and with_role returns an updated copy."""
    member = Member.join(DisplayName("Grace Hopper"), Email("grace@example.com"))
    promoted = member.with_role(Role.EDITOR)

    assert member.role == Role.VIEWER
    assert promoted.role == Role.EDITOR
    assert promoted.id == member.id


def test_project_lifecycle_attributes_and_membership() -> None:
    """Verify project creation, attribute updates, and member management."""
    owner = Member.join(DisplayName("Owner"), Email("owner@example.com"), Role.EDITOR)
    collaborator = Member.join(DisplayName("Collaborator"), Email("collab@example.com"))
    project = Project.create(name=ProjectName("Initial Name"), owner=owner)

    assert project.description is None
    assert project.settings.language == "en"

    project.rename(ProjectName("Updated Name"))
    assert project.name.value == "Updated Name"

    project.edit_description("Capstone project workspace")
    assert project.description == "Capstone project workspace"

    project.remove_description()
    assert project.description is None

    project.change_settings(ProjectSettings.create_default("es"))
    assert project.settings.language == "es"

    project.add_member(collaborator)
    assert project.get_member_by_name("Collaborator") is collaborator
    assert project.get_member_by_email("collab@example.com") is collaborator
    assert project.get_member_by_name("Unknown") is None
    assert project.get_member_by_email("unknown@example.com") is None

    project.edit_role(collaborator, Role.EDITOR)
    updated_member = project.get_member_by_email("collab@example.com")
    assert updated_member is not None
    assert updated_member.role == Role.EDITOR

    project.remove_member(updated_member)
    assert project.get_member_by_email("collab@example.com") is None


def test_project_transfer_ownership_rules() -> None:
    """Verify ownership transfer succeeds for members and fails for current owner or outsiders."""
    owner = Member.join(DisplayName("Owner"), Email("owner@example.com"), Role.EDITOR)
    member = Member.join(DisplayName("Member"), Email("member@example.com"))
    outsider = Member.join(DisplayName("Outsider"), Email("outsider@example.com"))
    project = Project.create(name=ProjectName("Alpha"), owner=owner)
    project.add_member(member)

    with pytest.raises(IsCurrentOwnerError):
        project.transfer_ownership(owner.id)

    with pytest.raises(NotAProjectMemberError):
        project.transfer_ownership(outsider.id)

    project.transfer_ownership(member.id)
    assert project.owner is member
