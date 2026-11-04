from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from .errors import (
    InvalidHeadingError,
    InvalidManuscriptIdError,
    InvalidManuscriptTitleError,
    InvalidProjectIdError,
    InvalidSectionIdError,
)

MAX_TITLE_LENGTH = 256
MAX_HEADING_LENGTH = 128


@dataclass(frozen=True)
class ManuscriptId:
    """A manuscript's identity. Enforces that its value is a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidManuscriptIdError(
                f"Invalid manuscript ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> ManuscriptId:
        """Generate a new random manuscript id."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ManuscriptId:
        """Parse a manuscript id from a string, raising InvalidManuscriptIdError if malformed."""
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidManuscriptIdError(
                f"Invalid manuscript ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass
class ProjectId:
    """A project's identity. Enforces that its value is a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidProjectIdError(
                f"Invalid project ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> ProjectId:
        """Generate a new random project id."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ProjectId:
        """Parse a project id from its string form, raising InvalidProjectIdError on failure."""
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidProjectIdError(
                f"Invalid project ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass
class ManuscriptTitle:
    """A manuscript title. Enforces non-blank text of at most MAX_TITLE_LENGTH characters."""

    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not stripped:
            raise InvalidManuscriptTitleError(
                "Manuscript title must not be blank. Enter at least one non-whitespace character."
            )

        length = len(stripped)

        if length > MAX_TITLE_LENGTH:
            raise InvalidManuscriptTitleError(
                f"Manuscript title is too long ({length} characters). Maximum is {MAX_TITLE_LENGTH}"
            )
        object.__setattr__(self, "value", stripped)


@dataclass
class SectionId:
    """A section's identity. Enforces that its value is a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidSectionIdError(
                f"Invalid section ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> SectionId:
        """Generate a new random section id."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> SectionId:
        """Parse a section id from its string form, raising InvalidSectionIdError on failure."""
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidSectionIdError(
                f"Invalid section ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass
class Heading:
    """A section heading. Enforces non-blank text of at most MAX_HEADING_LENGTH characters."""

    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        if not stripped:
            raise InvalidHeadingError(
                "Heading must not be blank. Enter at least one non-whitespace character."
            )

        length = len(stripped)

        if length > MAX_HEADING_LENGTH:
            raise InvalidHeadingError(
                f"Heading is too long ({length} characters). Maximum is {MAX_HEADING_LENGTH}"
            )
        object.__setattr__(self, "value", stripped)
