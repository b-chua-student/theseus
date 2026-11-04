from domain.shared.errors import DomainError


class SourceLibraryError(DomainError):
    """Base error for source library domain violations."""

    code = "source_library.error"


class InvalidAuthorNameError(SourceLibraryError):
    """Raised when an author name is blank."""

    code = "source_library.invalid_author_name"


class InvalidSourceTitleError(SourceLibraryError):
    """Raised when a source title is blank or too long."""

    code = "source_library.invalid_source_title"


class InvalidSourceIdError(SourceLibraryError):
    """Raised when a source ID is not a valid UUID."""

    code = "source_library.invalid_source_id"
