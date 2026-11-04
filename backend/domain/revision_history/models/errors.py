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
