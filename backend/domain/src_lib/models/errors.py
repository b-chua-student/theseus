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


class InvalidDescriptionError(SourceLibraryError):
    """Raised when a description is too long."""

    code = "source_library.invalid_description"


class InvalidTagsError(SourceLibraryError):
    """Raised when tags exceed the maximum count."""

    code = "source_library.invalid_tags"


class InvalidContentTypeError(SourceLibraryError):
    """Raised when content type is invalid."""

    code = "source_library.invalid_content_type"


class InvalidTextBodyError(SourceLibraryError):
    """Raised when text body is empty or exceeds length limit."""

    code = "source_library.invalid_text_body"
