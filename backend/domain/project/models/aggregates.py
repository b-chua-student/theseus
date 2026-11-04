from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.shared.clock import now

from .entities import Member
from .errors import IsCurrentOwnerError, NotAProjectMemberError
from .value_objects import MemberId, ProjectId, ProjectName, ProjectSettings, Role


@dataclass(eq=False)
class Project:
    """Aggregate root for a project: its name, owner, members, description and settings."""

    id: ProjectId
    name: ProjectName
    owner: Member
    description: str | None
    settings: ProjectSettings
    members: list[Member] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, name: ProjectName, owner: Member, description: str | None = None) -> Project:
        """Create a project with a fresh ID, default settings and no description."""
        return cls(
            id=ProjectId.new(),
            name=name,
            owner=owner,
            description=description,
            settings=ProjectSettings.create_default(),
        )

    # Project attributes

    def rename(self, new_name: ProjectName) -> None:
        """Set the project's name."""
        self.name = new_name

    def edit_description(self, text: str) -> None:
        """Set the project's description."""
        self.description = text

    def remove_description(self) -> None:
        """Clear the project's description."""
        self.description = None

    def change_settings(self, new_settings: ProjectSettings) -> None:
        """Replace the project's settings."""
        self.settings = new_settings

    # Ownership

    def transfer_ownership(self, new_owner_id: MemberId) -> None:
        """Make the member with new_owner_id the owner.

        Raises:
            IsCurrentOwnerError: If that member already owns the project.
            NotAProjectMemberError: If no matching member is found.
        """
        if self.owner.id == new_owner_id:
            raise IsCurrentOwnerError("Member is already the owner of this project.")

        for member in self.members:
            if member.id == new_owner_id:
                self.owner = member
                return

        raise NotAProjectMemberError("Member is not part of this project.")

    # Membership

    def add_member(self, new_member: Member) -> None:
        """Add a member to the project."""
        self.members.append(new_member)

    def remove_member(self, member: Member) -> None:
        """Remove a member from the project."""
        self.members.remove(member)

    def edit_role(self, member: Member, role: Role) -> None:
        """Change a member's role by replacing them with a copy holding the new role."""
        self.remove_member(member)
        self.add_member(member.with_role(role))

    def get_member_by_name(self, display_name: str) -> Member | None:
        """Return the first member whose display name matches, or None."""
        for member in self.members:
            if member.display_name == display_name:
                return member
        return None

    def get_member_by_email(self, email: str) -> Member | None:
        """Return the first member whose email matches, or None."""
        for member in self.members:
            if member.email == email:
                return member
        return None
