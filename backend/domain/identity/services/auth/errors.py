from domain.shared.errors import ServiceError

class InvalidCredentialsError(ServiceError):
    def __init__(self, reason: str = "") -> None:
        super().__init__("Invalid credentials")
        self.reason = reason

class RegistrationValidationError(ServiceError):
    pass

class EmailAlreadyRegisteredError(ServiceError):
    pass

class WeakPasswordError(ServiceError):
    pass
