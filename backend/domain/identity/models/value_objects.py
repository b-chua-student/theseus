from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email

from .errors import InvalidDisplayNameError, InvalidEmailError, InvalidPasswordHashError


@dataclass(frozen=True)
class UserId:
    """Unique user identifier; the value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise TypeError("UserId.value must be a UUID")

    @classmethod
    def new(cls) -> UserId:
        """Generate a new random UserId."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> UserId:
        """Parse a UserId from its UUID string form."""
        return cls(UUID(text))


@dataclass(frozen=True)
class DisplayName:
    """User display name, stripped and between 1 and 50 characters."""

    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not stripped:
            raise InvalidDisplayNameError("must not be blank")
        if len(stripped) > 50:
            raise InvalidDisplayNameError("must be at most 50 characters")
        object.__setattr__(self, "value", stripped)


@dataclass(frozen=True)
class Email:
    """Email address, validated and normalized on creation."""

    value: str

    def __post_init__(self) -> None:
        try:
            info = validate_email(self.value, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidEmailError("Email is not valid.") from e
        object.__setattr__(self, "value", info.normalized)

    def __str__(self) -> str:
        return self.value


FORMAT_CHECK = "$argon2"


@dataclass(frozen=True)
class PasswordHash:
    """Password hash; the value must be in Argon2 format."""

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value.startswith(FORMAT_CHECK):
            raise InvalidPasswordHashError("Not a recognized hash format.")
