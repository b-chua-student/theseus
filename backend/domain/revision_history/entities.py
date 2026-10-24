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
        """Validate the revision's parent relationships.

        Raises:
            ValueError: If the revision has more than two parents, references
                itself as a parent, or contains duplicate parent IDs.
        """
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
        """Normalize and validate the branch name.

        Strips leading and trailing whitespace from the branch name.

        Raises:
            ValueError: If the branch name is empty after stripping
                whitespace.
        """
        self.name = self.name.strip()

        if not self.name:
            raise ValueError("Branch name cannot be empty")

    def advance_to(self, revision_id: UUID) -> None:
        """Update the branch head to reference a new revision.

        Args:
            revision_id: UUID of the revision to reference.
        """
        self.head_id = revision_id


@dataclass(frozen=True, slots=True)
class Milestone:
    """A named marker for an important revision."""

    name: str
    revision_id: UUID

    def __post_init__(self) -> None:
        """Validate the milestone name.

        Raises:
            ValueError: If the milestone name contains only whitespace.
        """
        if not self.name.strip():
            raise ValueError("Milestone name cannot be empty")
