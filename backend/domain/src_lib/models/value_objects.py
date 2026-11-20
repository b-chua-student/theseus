from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4

from .errors import (
    InvalidAuthorNameError,
    InvalidDescriptionError,
    InvalidSourceIdError,
    InvalidSourceTitleError,
    InvalidTagsError,
    InvalidTextBodyError,
)


@dataclass(frozen=True)
class SourceId:
    """Identifier of a source; the value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Perform post-initialization validation."""
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
        """Perform post-initialization validation."""
        if not self.name.strip():
            raise InvalidAuthorNameError("Author name cannot be empty")


MAX_SOURCE_TITLE_LENGTH = 256


@dataclass(frozen=True)
class SourceTitle:
    """Title of a source; stripped, non-blank, and at most 256 characters."""

    value: str

    def __post_init__(self) -> None:
        """Perform post-initialization validation."""
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


MAX_DESCRIPTION_LENGTH = 1000


@dataclass(frozen=True)
class Description:
    """Optional description of a text source; at most 1000 characters."""

    value: str

    def __post_init__(self) -> None:
        """Perform post-initialization validation."""
        if self.value is None:
            object.__setattr__(self, "value", "")
            return

        stripped = self.value.strip()
        length = len(stripped)

        if length > MAX_DESCRIPTION_LENGTH:
            raise InvalidDescriptionError(
                f"Description is too long ({length} characters). "
                f"Maximum is {MAX_DESCRIPTION_LENGTH}"
            )
        object.__setattr__(self, "value", stripped)

    @classmethod
    def create(cls, value: str | None) -> Description | None:
        """Create a Description if value is not None and not empty, else None."""
        if value is None or not value.strip():
            return None
        return cls(value)


@dataclass(frozen=True)
class Tags:
    """Collection of tags for a source; deduplicated, trimmed, ≤10 tags."""

    value: tuple[str, ...]

    def __post_init__(self) -> None:
        # Strip and filter out empty tags
        """Perform post-initialization validation."""
        tags = [tag.strip() for tag in self.value if tag.strip()]

        # Deduplicate while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        if len(unique_tags) > 10:
            raise InvalidTagsError(f"Too many tags ({len(unique_tags)}). Maximum is 10.")

        object.__setattr__(self, "value", tuple(unique_tags))

    @classmethod
    def create(cls, tags: list[str] | None) -> Tags:
        """Create Tags from a list of strings, handling None/empty."""
        if not tags:
            return cls(())
        return cls(tuple(tags))


class ContentType(Enum):
    """Type of content for text sources."""

    DOCUMENTATION = "documentation"
    NOTES = "notes"
    CODE = "code"
    OTHER = "other"

    @classmethod
    def from_str(cls, value: str | None) -> ContentType:
        """Parse from string, defaulting to OTHER."""
        if value is None:
            return cls.OTHER

        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


@dataclass(frozen=True)
class TextBody:
    """Text content of a source; 1-100,000 characters, UTF-8."""

    value: str

    def __post_init__(self) -> None:
        """Perform post-initialization validation."""
        if not self.value.strip():
            raise InvalidTextBodyError("Text content cannot be empty")

        length = len(self.value)

        if length > 100000:
            raise InvalidTextBodyError(
                f"Text content is too long ({length} characters). Maximum is 100,000"
            )
        # Store as-is, preserving whitespace and encoding
        object.__setattr__(self, "value", self.value)
