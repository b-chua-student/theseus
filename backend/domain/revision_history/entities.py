from dataclasses import dataclass
from uuid import UUID

from .value_objects import CommitMessage, Snapshot


@dataclass(frozen=True, slots=True)
class Revision:
    """An immutable commit in the manuscript history."""

    id: UUID
    parent_ids: tuple[UUID, ...]
    message: CommitMessage
    snapshot: Snapshot

    def __post_init__(self) -> None:
        if len(self.parent_ids) > 2:
            raise ValueError("A revision can have at most two parents")

        if self.id in self.parent_ids:
            raise ValueError("A revision cannot be its own parent")

        if len(set(self.parent_ids)) != len(self.parent_ids):
            raise ValueError("Duplicate parent revisions are not allowed")


@dataclass(eq=False)
class Branch:
    """A mutable reference to the current revision of a branch."""

    name: str
    head_id: UUID

    def __post_init__(self) -> None:
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Branch name cannot be empty")

    def advance_to(self, revision_id: UUID) -> None:
        """Update the branch head."""
        self.head_id = revision_id


@dataclass(frozen=True, slots=True)
class Milestone:
    """A named marker for an important revision."""

    name: str
    revision_id: UUID

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Milestone name cannot be empty")
