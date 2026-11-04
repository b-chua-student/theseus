from domain.shared.errors import DomainError


class ManuscriptError(DomainError):
    """Base class for manuscript domain errors."""

    code = "manuscript.error"


class InvalidManuscriptIdError(ManuscriptError):
    """Raised when a manuscript ID is not a valid UUID."""

    code = "manuscript.invalid_manuscript_id"


class InvalidProjectIdError(ManuscriptError):
    """Raised when a project ID is not a valid UUID."""

    code = "manuscript.invalid_project_id"


class InvalidManuscriptTitleError(ManuscriptError):
    """Raised when a manuscript title is blank or too long."""

    code = "manuscript.invalid_manuscript_title"


class InvalidSectionIdError(ManuscriptError):
    """Raised when a section ID is not a valid UUID."""

    code = "manuscript.invalid_section_id"


class InvalidHeadingError(ManuscriptError):
    """Raised when a section heading is blank or too long."""

    code = "manuscript.invalid_heading"
