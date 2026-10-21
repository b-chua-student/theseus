from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Immutable reference to a complete manuscript state."""

    tree_hash: str

    def __post_init__(self) -> None:
        if not self.tree_hash.strip():
            raise ValueError("Snapshot tree hash cannot be empty")


@dataclass(frozen=True, slots=True)
class CommitMessage:
    """Description of a revision."""

    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Commit message cannot be empty")


@dataclass(frozen=True, slots=True)
class DiffHunk:
    """A change to a section between two revisions."""

    section_id: UUID
    before: str
    after: str


@dataclass(frozen=True, slots=True)
class MergeConflict:
    """A conflicting change detected during a merge."""

    section_id: UUID
    base: str
    ours: str
    theirs: str
