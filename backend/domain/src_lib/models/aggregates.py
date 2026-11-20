from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from .events import SourceAdded, SourceRemoved, SourceUpdated
from .value_objects import (
    Author,
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


@dataclass
class Source:
    """Aggregate root for a bibliographic source attached to a project.

    Removal is a soft delete; a removed source cannot have its metadata updated.

    For text sources (kind="text"), content is required and file_ref must be None.
    For file sources (kind="file"), file_ref is required and content must be None.
    """

    id: SourceId
    title: SourceTitle
    authors: tuple[Author, ...]
    year: int | None
    file_ref: str | None
    project_id: UUID
    removed_at: datetime | None = None
    # New fields for text sources
    kind: Literal["file", "text"] = "file"
    content: TextBody | None = None
    description: Description | None = None
    tags: Tags = field(default_factory=lambda: Tags(()))
    content_type: ContentType = ContentType.OTHER
    version: int = 1
    updated_at: datetime | None = None
    created_at: datetime | None = None
    _events: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate invariants for text vs file sources."""
        if self.kind == "text":
            if self.content is None:
                raise ValueError("Text source must have content")
            if self.file_ref:
                raise ValueError("Text source cannot have file_ref")
        elif self.kind == "file":
            if not self.file_ref:
                raise ValueError("File source must have file_ref")
            if self.content is not None:
                raise ValueError("File source cannot have content")
        else:
            raise ValueError(f"Invalid kind: {self.kind}")

        # Set updated_at if not provided
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", datetime.now(UTC))
        if self.created_at is None:
            object.__setattr__(self, "created_at", self.updated_at)

    @classmethod
    def add(
        cls,
        title: SourceTitle,
        file_ref: str | None,
        project_id: UUID,
        authors: list[Author] | None = None,
        year: int | None = None,
        kind: Literal["file", "text"] = "file",
        content: TextBody | None = None,
        description: Description | None = None,
        tags: Tags | None = None,
        content_type: ContentType = ContentType.OTHER,
    ) -> Source:
        """Create a new source and record a SourceAdded event.

        Raises:
            ValueError: if `file_ref` is empty for file sources,
                or if `content` is empty for text sources.
        """
        if kind == "file" and not file_ref:
            raise ValueError("File reference required for file sources")
        if kind == "text" and content is None:
            raise ValueError("Content required for text sources")

        source = cls(
            id=SourceId.new(),
            title=title,
            authors=tuple(authors or ()),
            year=year,
            file_ref=file_ref,
            project_id=project_id,
            kind=kind,
            content=content,
            description=description,
            tags=tags or Tags(()),
            content_type=content_type,
            updated_at=datetime.now(UTC),
        )
        source._events.append(SourceAdded(source.id, project_id, file_ref, kind))
        return source

    @classmethod
    def add_text(
        cls,
        title: SourceTitle,
        content: TextBody,
        project_id: UUID,
        description: Description | None = None,
        tags: Tags | None = None,
        content_type: ContentType = ContentType.OTHER,
    ) -> Source:
        """Create a new text source (convenience method)."""
        return cls.add(
            title=title,
            file_ref=None,  # Text sources have no file (D6)
            project_id=project_id,
            authors=None,
            year=None,
            kind="text",
            content=content,
            description=description,
            tags=tags,
            content_type=content_type,
        )

    def update_text(
        self,
        title: SourceTitle,
        content: TextBody,
        description: Description | None = None,
        tags: Tags | None = None,
        content_type: ContentType = ContentType.OTHER,
    ) -> None:
        """Replace the source's text fields and bump version.

        Raises:
            ValueError: if the source has been removed or is not a text source.
        """
        self._ensure_active()
        if self.kind != "text":
            raise ValueError("Can only update text on text sources")

        self.title = title
        self.content = content
        self.description = description
        self.tags = tags or Tags(())
        self.content_type = content_type
        self.version += 1
        self.updated_at = datetime.now(UTC)

        self._events.append(SourceUpdated(self.id, self.project_id, self.kind, self.version))

    def update_metadata(self, title: SourceTitle, authors: list[Author], year: int | None) -> None:
        """Replace the source's title, authors and year.

        Raises:
            ValueError: if the source has been removed.
        """
        self._ensure_active()
        self.title, self.authors, self.year = title, tuple(authors), year
        if self.kind == "text":
            self.updated_at = datetime.now(UTC)
            self.version += 1
            self._events.append(SourceUpdated(self.id, self.project_id, self.kind, self.version))

    def remove(self) -> None:
        """Soft-delete the source and record a SourceRemoved event; idempotent."""
        if self.removed_at:
            return
        self.removed_at = datetime.now(UTC)
        self._events.append(SourceRemoved(self.id, self.project_id))

    @property
    def is_removed(self) -> bool:
        """Whether the source has been removed."""
        return self.removed_at is not None

    def pull_events(self) -> list:
        """Return and clear the pending domain events."""
        events, self._events = self._events, []
        return events

    def _ensure_active(self) -> None:
        if self.is_removed:
            raise ValueError("Source is removed")
