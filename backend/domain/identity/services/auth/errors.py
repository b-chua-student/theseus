from domain.shared.errors import ServiceError


class InvalidCredentialsError(ServiceError):
    """Raised when login fails; the reason is kept for logging only."""

    def __init__(self, reason: str = "") -> None:
        super().__init__("Invalid credentials")
        self.reason = reason


class RegistrationValidationError(ServiceError):
    """Raised when registration input fails validation."""

    pass


class EmailAlreadyRegisteredError(ServiceError):
    """Raised when registering an email that already has an account."""

    pass


class WeakPasswordError(ServiceError):
    """Raised when a password does not meet the strength requirements."""

    pass
