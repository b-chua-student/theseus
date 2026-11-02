from .value_objects import Role, MemberId, DisplayName, Email

from dataclasses import dataclass, field, replace
from datetime import datetime

from domain.shared.clock import now

@dataclass(eq=False)
class Member:
    id: MemberId
    display_name: DisplayName
    email: Email
    role: Role
    joined_at: datetime = field(default_factory=now)

    @classmethod
    def join(cls, display_name: DisplayName, email: Email, role: Role = Role.VIEWER) -> Member:
        return cls(
            id=MemberId.new(),
            display_name=display_name,
            email=email,
            role=role
        )

    def with_role(self, new_role: Role) -> Member:
        return replace(self, role=new_role)
