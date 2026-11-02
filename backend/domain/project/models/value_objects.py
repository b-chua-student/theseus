from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from .errors import (
    InvalidDisplayNameError,
    InvalidEmailError,
    InvalidProjectNameError,
)
from email_validator import validate_email, EmailNotValidError

class Role(Enum):
    VIEWER = 0
    EDITOR = 1

@dataclass(frozen=True)
class ProjectId:
    value: UUID

    @classmethod
    def new(cls) -> ProjectId:
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ProjectId:
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
    language: str

    @classmethod
    def create_default(cls, language: str = "en") -> ProjectSettings:
        return cls(language=language)


@dataclass(frozen=True)
class MemberId:
    value: UUID

    @classmethod
    def new(cls) -> MemberId:
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> MemberId:
        return cls(UUID(text))

@dataclass(frozen=True)
class DisplayName:
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
    value: str

    def __post_init__(self) -> None:
        try:
            info = validate_email(self.value, check_deliverability=False)
        except EmailNotValidError as e:
            raise InvalidEmailError("Email is not valid.") from e
        object.__setattr__(self, "value", info.normalized)

    def __str__(self) -> str:
        return self.value
