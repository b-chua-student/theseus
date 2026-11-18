from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from domain.shared.clock import now

from .value_objects import DisplayName, Email, MemberId, Role


@dataclass(eq=False)
class Member:
    """A person participating in a project with a role; identity is by id, not value."""

    id: MemberId
    display_name: DisplayName
    email: Email
    role: Role
    joined_at: datetime = field(default_factory=now)

    @classmethod
    def join(cls, display_name: DisplayName, email: Email, role: Role = Role.VIEWER) -> Member:
        """Create a member with a new ID; defaults to the VIEWER role."""
        return cls(id=MemberId.new(), display_name=display_name, email=email, role=role)

    def with_role(self, new_role: Role) -> Member:
        """Return a copy of this member with the given role."""
        return replace(self, role=new_role)
