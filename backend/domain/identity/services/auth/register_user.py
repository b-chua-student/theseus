from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.infrastructure.ports.password_hasher import PasswordHasher
from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import DisplayName, Email, PasswordHash

from .errors import EmailAlreadyRegisteredError, WeakPasswordError


class RegisterUserService:
    """Use case for registering a new user."""

    def __init__(self, repository: IdentityRepository, hasher: PasswordHasher) -> None:
        self._repository = repository
        self._hasher = hasher

    def execute(self, display_name: str, email: str, password: str) -> User:
        """Create and store a new user, returning it.

        Raises:
            WeakPasswordError: If the password is shorter than 8 characters.
            EmailAlreadyRegisteredError: If the email is already in use.
        """
        valid_display_name = DisplayName(display_name)
        valid_email = Email(email)

        if len(password) < 8:
            raise WeakPasswordError()

        if self._repository.get_by_email(valid_email) is not None:
            raise EmailAlreadyRegisteredError()

        password_hash = PasswordHash(self._hasher.hash(password))

        user = User.register(
            display_name=valid_display_name, email=valid_email, password_hash=password_hash
        )

        self._repository.add_user(user)

        return user
