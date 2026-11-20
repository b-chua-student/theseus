from domain.shared.errors import ServiceError


class ManuscriptNotFound(ServiceError):
    """Raised when the manuscript to version does not exist."""


class HistoryNotFound(ServiceError):
    """Raised when a manuscript has no revision history yet."""
