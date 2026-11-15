from domain.shared.errors import DomainError


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
    code = "revision.draft_not_found"


class NoSharedHistoryError(RevisionError):
    code = "revision.no_shared_history"


class UnsavedChangesError(RevisionError):
    code = "revision.unsaved_changes"


class MergeInProgressError(RevisionError):
    code = "revision.merge_in_progress"


class ConcurrentModificationError(RevisionError):
    code = "revision.concurrent_modification"


class MergeConflictError(RevisionError):
    code = "revision.merge_conflict"

    def __init__(self, conflicts):
        super().__init__("Resolve the conflicts before merging.")
        self.conflicts = conflicts


class InvalidResolutionError(RevisionError):
    code = "revision.invalid_resolution"

    def __init__(self, kind, section_id, field):
        super().__init__("Invalid merge resolution.")
        self.details = {"kind": kind, "section_id": str(section_id), "field": field}
