from domain.shared.errors import DomainError

class IdentityError(DomainError):
    pass

class InvalidDisplayNameError(IdentityError):
    pass

class InvalidEmailError(IdentityError):
    pass

class InvalidPasswordHashError(IdentityError):
    pass
