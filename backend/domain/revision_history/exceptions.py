class RevisionHistoryError(Exception):
    """Base exception for revision-history domain errors."""


class BranchNotFoundError(RevisionHistoryError):
    """The requested branch does not exist."""


class RevisionNotFoundError(RevisionHistoryError):
    """The requested revision does not exist."""


class MilestoneNotFoundError(RevisionHistoryError):
    """The requested milestone does not exist."""


class DuplicateBranchError(RevisionHistoryError):
    """A branch with the same name already exists."""


class DuplicateMilestoneError(RevisionHistoryError):
    """A milestone with the same name already exists."""


class MergeConflictError(RevisionHistoryError):
    """A merge contains unresolved conflicts."""


class InvalidRevisionError(RevisionHistoryError):
    """A revision violates history constraints."""
