from domain.shared.errors import DomainError


class IdentityError(DomainError):
    """Base class for identity domain errors."""

    pass


class InvalidDisplayNameError(IdentityError):
    """Raised when a display name is blank or too long."""

    pass


class InvalidEmailError(IdentityError):
    """Raised when an email address is not valid."""

    pass


class InvalidPasswordHashError(IdentityError):
    """Raised when a password hash is not in a recognized format."""

    pass
