from domain.shared.errors import DomainError


class ManuscriptNotFoundError(DomainError):
    """Raised when a requested manuscript does not exist."""

    code = "manuscript.not_found"
