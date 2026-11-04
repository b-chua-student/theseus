from domain.shared.errors import DomainError


class ProjectError(DomainError):
    """Base class for project domain errors."""


class InvalidProjectNameError(ProjectError):
    """Raised when a project name is blank or too long."""


class InvalidDisplayNameError(ProjectError):
    """Raised when a display name is blank or too long."""


class InvalidEmailError(ProjectError):
    """Raised when an email address is not valid."""


class NotAProjectMemberError(ProjectError):
    """Raised when a user is not a member of the project."""


class IsCurrentOwnerError(ProjectError):
    """Raised when ownership is transferred to the member who already owns the project."""
