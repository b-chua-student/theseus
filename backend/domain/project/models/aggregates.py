from dataclasses import dataclass, field
from datetime import datetime

from .value_objects import ProjectId, ProjectName, ProjectSettings, Role, MemberId
from .entities import Member
from .errors import (
    NotAProjectMemberError,
    IsCurrentOwnerError
)

from domain.shared.clock import now

@dataclass(eq=False)
class Project:
    id: ProjectId
    name: ProjectName
    owner: Member
    description: str | None
    settings: ProjectSettings 
    members: list[Member] = field(default_factory=list)
    created_at: datetime = field(default_factory=now)

    @classmethod
    def create(cls, name: ProjectName, owner: Member, description: str | None = None) -> Project:
        return cls(
            id=ProjectId.new(),
            name=name,
            owner=owner,
            description=description,
            settings=ProjectSettings.create_default(),
        )

    # Project attributes

    def rename(self, new_name: ProjectName) -> None:
        self.name = new_name 

    def edit_description(self, text: str) -> None:
        self.description = text

    def remove_description(self) -> None:
        self.description = None

    def change_settings(self, new_settings: ProjectSettings) -> None:
        self.settings = new_settings

    # Ownership
    
    def transfer_ownership(self, new_owner_id: MemberId) -> None:
        if self.owner.id == new_owner_id:
            raise IsCurrentOwnerError()

        for member in self.members:
            if member.id == new_owner_id:
                self.owner = member
            else:
                raise NotAProjectMemberError()

    # Membership

    def add_member(self, new_member: Member):
        self.members.append(new_member)
    
    def remove_member(self, member: Member):
        self.members.remove(member)

    def edit_role(self, member: Member, role: Role):
        self.remove_member(member)
        self.add_member(member.with_role(role))

    def get_member_by_name(self, display_name: str) -> Member | None:
        for member in self.members:
            if member.display_name == display_name:
                return member
            else:
                return None

    def get_member_by_email(self, email: str) -> Member | None:
        for member in self.members:
            if member.email == email:
                return member
            else:
                return None
