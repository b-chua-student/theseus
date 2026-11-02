from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.identity.models.aggregates import User
from domain.identity.models.errors import InvalidEmailError
from domain.identity.models.value_objects import Email
from domain.identity.services.auth.errors import InvalidCredentialsError


class LoginUserService:
    def __init__(self, repository: IdentityRepository, hasher: PasswordHasher) -> None:
        self._repository = repository
        self._hasher = hasher
        self._dummy_hash = hasher.hash("dummy-password")

    def execute(self, email: str, password: str) -> User:
        try:
            email_vo = Email(email)
        except InvalidEmailError:
            self._hasher.verify(password, self._dummy_hash)
            raise InvalidCredentialsError("Invalid email format")

        user = self._repository.get_by_email(email_vo)

        if user is None:
            self._hasher.verify(password, self._dummy_hash)
            raise InvalidCredentialsError("Unknown email")

        if not self._hasher.verify(password, user.password_hash.value):
            raise InvalidCredentialsError("Wrong password")

        return user
