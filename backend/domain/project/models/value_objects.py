from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email

from .errors import (
    InvalidDisplayNameError,
    InvalidEmailError,
    InvalidProjectNameError,
)


class Role(Enum):
    """Permission level of a project member."""

    VIEWER = 0
    EDITOR = 1


@dataclass(frozen=True)
class ProjectId:
    """Immutable identifier of a project, backed by a UUID."""

    value: UUID

    @classmethod
    def new(cls) -> ProjectId:
        """Generate a new random project ID."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ProjectId:
        """Parse a project ID from its UUID string form."""
        return cls(value=UUID(text))


@dataclass(frozen=True, slots=True)
class ProjectName:
    """Immutable project name."""

    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not stripped:
            raise InvalidProjectNameError("must not be blank")
        if len(stripped) > 256:
            raise InvalidProjectNameError("must be at most 50 characters")
        object.__setattr__(self, "value", stripped)


@dataclass(frozen=True)
class ProjectSettings:
    """Immutable project settings."""

    language: str

    @classmethod
    def create_default(cls, language: str = "en") -> ProjectSettings:
        """Return settings with the given language (default "en")."""
        return cls(language=language)


@dataclass(frozen=True)
class MemberId:
    """Immutable identifier of a project member, backed by a UUID."""

    value: UUID

    @classmethod
    def new(cls) -> MemberId:
        """Generate a new random member ID."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> MemberId:
        """Parse a member ID from its UUID string form."""
        return cls(UUID(text))


@dataclass(frozen=True)
class DisplayName:
    """Immutable member display name; stripped, non-blank and at most 50 characters."""

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
    """Immutable email address; validated and normalized without a deliverability check."""

    value: str

    def __post_init__(self) -> None:
        try:
            info = validate_email(self.value, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidEmailError("Email is not valid.") from e
        object.__setattr__(self, "value", info.normalized)

    def __str__(self) -> str:
        return self.value
