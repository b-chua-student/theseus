from domain.shared.errors import DomainError


class SourceNotFoundError(DomainError):
    """Raised when a requested source does not exist."""

    code = "source_library.not_found"
