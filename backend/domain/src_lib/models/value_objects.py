from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from .errors import InvalidAuthorNameError, InvalidSourceIdError, InvalidSourceTitleError


@dataclass(frozen=True)
class SourceId:
    """Identifier of a source; the value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidSourceIdError(
                f"Invalid manuscript ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> SourceId:
        """Generate a new random ID."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> SourceId:
        """Parse an ID from its UUID string form.

        Raises:
            InvalidSourceIdError: if the text is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidSourceIdError(
                f"Invalid manuscript ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass(frozen=True)
class Author:
    """Author of a source; the name must not be blank."""

    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidAuthorNameError("Author name cannot be empty")


MAX_SOURCE_TITLE_LENGTH = 256


@dataclass(frozen=True)
class SourceTitle:
    """Title of a source; stripped, non-blank, and at most 256 characters."""

    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not stripped:
            raise InvalidSourceTitleError(
                "Manuscript title must not be blank. Enter at least one non-whitespace character."
            )

        length = len(stripped)

        if length > MAX_SOURCE_TITLE_LENGTH:
            raise InvalidSourceTitleError(
                f"Manuscript title is too long ({length} characters). "
                f"Maximum is {MAX_SOURCE_TITLE_LENGTH}"
            )
        object.__setattr__(self, "value", stripped)
