from domain.shared.errors import DomainError


class ProjectNotFoundError(DomainError):
    """Raised when a requested project does not exist."""
