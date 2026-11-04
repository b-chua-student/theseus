from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from .events import SourceAdded, SourceRemoved
from .value_objects import Author, SourceId, SourceTitle


@dataclass
class Source:
    """Aggregate root for a bibliographic source attached to a project.

    Removal is a soft delete; a removed source cannot have its metadata updated.
    """

    id: SourceId
    title: SourceTitle
    authors: tuple[Author, ...]
    year: int | None
    file_ref: str
    project_id: UUID
    removed_at: datetime | None = None
    _events: list = field(default_factory=list, init=False, repr=False)

    @classmethod
    def add(
        cls,
        title: SourceTitle,
        file_ref: str,
        project_id: UUID,
        authors: list[Author] | None = None,
        year: int | None = None,
    ) -> Source:
        """Create a new source and record a SourceAdded event.

        Raises:
            ValueError: if `file_ref` is empty.
        """
        if not file_ref:
            raise ValueError("File reference required")
        source = cls(SourceId.new(), title, tuple(authors or ()), year, file_ref, project_id)
        source._events.append(SourceAdded(source.id, project_id, file_ref))
        return source

    def update_metadata(self, title: SourceTitle, authors: list[Author], year: int | None) -> None:
        """Replace the source's title, authors and year.

        Raises:
            ValueError: if the source has been removed.
        """
        self._ensure_active()
        self.title, self.authors, self.year = title, tuple(authors), year

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
