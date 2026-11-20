from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UserDTO:
    """Read-only snapshot of a user exposed to other bounded contexts."""

    id: str
    display_name: str
    email: str


class IdentityAPI(Protocol):
    """Public contract through which other contexts look up users."""

    def get_user(self, user_id: str) -> UserDTO | None:
        """Return the user with the given id, or None if not found."""
        ...

    def get_users(self, user_ids: list[str]) -> list[UserDTO]:
        """Return the users matching the given ids."""
        ...
