from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from domain.shared.errors import DomainError

if TYPE_CHECKING:
    from .merge import Conflict


class RevisionError(DomainError):
    """Base error for revision history domain violations."""

    code = "revision.error"


class InvalidManuscriptIdError(RevisionError):
    """Raised when a manuscript ID is not a valid UUID."""

    code = "revision.invalid_manuscript_id"


class InvalidRevisionIdError(RevisionError):
    """Raised when a revision ID is not a valid UUID."""

    code = "revision.invalid_revision_id"


class NoChangesError(RevisionError):
    """Raised when committing a revision with no changes since the last one."""

    code = "revision.no_changes"


class DraftNotFoundError(RevisionError):
    """Raised when a named draft does not exist."""

    code = "revision.draft_not_found"


class NoSharedHistoryError(RevisionError):
    """Raised when the drafts have no shared revision history."""

    code = "revision.no_shared_history"


class UnsavedChangesError(RevisionError):
    """Raised when the working manuscript differs from the current draft head."""

    code = "revision.unsaved_changes"


class MergeInProgressError(RevisionError):
    """Raised when another merge holds the manuscript lock."""

    code = "revision.merge_in_progress"


class ConcurrentModificationError(RevisionError):
    """Raised when the stored history version changes during an operation."""

    code = "revision.concurrent_modification"


class MergeConflictError(RevisionError):
    """Raised when a merge has unresolved conflicts."""

    code = "revision.merge_conflict"

    def __init__(self, conflicts: list[Conflict]) -> None:
        """Record the conflicts the caller must resolve."""
        super().__init__("Resolve the conflicts before merging.")
        self.conflicts = conflicts


class InvalidResolutionError(RevisionError):
    """Raised when a submitted conflict resolution is invalid."""

    code = "revision.invalid_resolution"

    def __init__(self, kind: str, section_id: UUID, field: str) -> None:
        """Record the reason, section ID, and field for the invalid resolution."""
        super().__init__("Invalid merge resolution.")
        self.details = {"kind": kind, "section_id": str(section_id), "field": field}
