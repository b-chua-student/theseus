from email_validator import validate_email, EmailNotValidError

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .errors import InvalidDisplayNameError, InvalidEmailError, InvalidPasswordHashError


@dataclass(frozen=True)
class UserId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise TypeError("UserId.value must be a UUID")

    @classmethod
    def new(cls) -> UserId:
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> UserId:
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

FORMAT_CHECK = "$argon2"

@dataclass(frozen=True)
class PasswordHash:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.value.startswith(FORMAT_CHECK):
            raise InvalidPasswordHashError("Not a recognized hash format.")
