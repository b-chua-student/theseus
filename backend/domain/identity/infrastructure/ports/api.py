from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class UserDTO:
    id: str
    display_name: str
    email: str

class IdentityAPI(Protocol):
    def get_user(self, user_id: str) -> UserDTO | None: ...
    def get_users(self, user_ids: list[str]) -> list[UserDTO]: ...
