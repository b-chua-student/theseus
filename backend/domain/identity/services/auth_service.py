from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from domain.identity.infrastructure.ports.identity_repository import IdentityRepository
from domain.identity.models.aggregates import User
from domain.identity.models.errors import InvalidEmailError
from domain.identity.models.value_objects import Email

_hasher = PasswordHasher()
# Verified against when the email is unknown, so response time doesn't reveal it
_DUMMY_HASH = _hasher.hash("dummy-password")


class AuthService:
    """Legacy service for authenticating users against a repository."""

    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    def authenticate(self, email: str, password: str) -> User | None:
        """Return the user if the password matches, otherwise None."""
        try:
            user = self.repository.get_by_email(Email(email))
        except InvalidEmailError:
            return None
        hash_to_check = user.password_hash.value if user and user.password_hash else _DUMMY_HASH

        try:
            _hasher.verify(hash_to_check, password)
        except (VerifyMismatchError, InvalidHashError):
            return None

        if user is None or not user.password_hash:
            return None  # unknown email or OAuth-only account
        return user
