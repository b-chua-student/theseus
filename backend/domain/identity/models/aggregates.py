from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.shared.clock import now

from .value_objects import DisplayName, Email, PasswordHash, UserId


@dataclass(eq=False)
class User:
    """Account aggregate root, identified by its UserId."""

    id: UserId
    display_name: DisplayName
    email: Email
    password_hash: PasswordHash = field(repr=False)
    verified: bool = False
    created_at: datetime = field(default_factory=now)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def register(cls, email: Email, display_name: DisplayName, password_hash: PasswordHash) -> User:
        """Create a new, unverified user with a freshly generated id."""
        return cls(
            id=UserId.new(),
            email=email,
            display_name=display_name,
            password_hash=password_hash,
        )

    def verify_email(self) -> None:
        """Mark the user's email as verified."""
        self.verified = True

    def change_email(self, email: Email) -> None:
        """Replace the email and reset verification."""
        self.email = email
        self.verified = False

    def change_password(self, new_hash: PasswordHash) -> None:
        """Replace the password hash."""
        self.password_hash = new_hash
