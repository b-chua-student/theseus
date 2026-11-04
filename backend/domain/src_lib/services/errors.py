from domain.shared.errors import ServiceError


class SourceNotFound(ServiceError):
    """Raised when the targeted source does not exist."""

    code = "source_library.source_not_found"
