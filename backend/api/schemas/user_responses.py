from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.user.aggregates import User


@dataclass(frozen=True)
class UserResponseDTO:
    """Immutable response DTO representing a user.

    Attributes:
        id: Unique identifier of the user.
        email: Email address of the user.
        display_name: Display name of the user.
    """

    id: UUID
    email: str
    display_name: str

    @classmethod
    def from_domain(cls, user: User) -> UserResponseDTO:
        """Build a DTO from a domain user.

        Args:
            user: User aggregate to convert.

        Returns:
            DTO populated from the user.
        """
        return cls(
            id=user.id,
            email=user.email.value,
            display_name=user.display_name.value,
        )

    def to_dict(self) -> dict:
        """Serialize the DTO to a JSON-compatible dictionary.

        Returns:
            Dictionary with UUIDs converted to strings.
        """
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
        }
