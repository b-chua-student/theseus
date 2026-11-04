from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from .errors import InvalidManuscriptIdError, InvalidRevisionIdError


@dataclass(frozen=True)
class ManuscriptId:
    """Identifier of a manuscript; the value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidManuscriptIdError(
                f"Invalid manuscript ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> ManuscriptId:
        """Generate a new random ID."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ManuscriptId:
        """Parse an ID from its UUID string form.

        Raises:
            InvalidManuscriptIdError: if the text is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidManuscriptIdError(
                f"Invalid manuscript ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass(frozen=True)
class RevisionId:
    """Identifier of a revision; the value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidRevisionIdError(
                f"Invalid manuscript ID '{self.value}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            )

    @classmethod
    def new(cls) -> RevisionId:
        """Generate a new random ID."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> RevisionId:
        """Parse an ID from its UUID string form.

        Raises:
            InvalidRevisionIdError: if the text is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidRevisionIdError(
                f"Invalid manuscript ID '{text}'. "
                "Expected a UUID, e.g. '123e4567-e89b-12d3-a456-426614174000'"
            ) from None


@dataclass(frozen=True)
class SectionSnapshot:
    """Immutable copy of one manuscript section's structure and body."""

    id: UUID
    parent_id: UUID | None
    heading: str
    ordinal: int
    body: str


@dataclass(frozen=True)
class Snapshot:
    """Immutable copy of all of a manuscript's sections at a point in time."""

    sections: tuple[SectionSnapshot, ...]
