from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from domain.identity.models.aggregates import User
from repositories.identity.identity_repository import IdentityRepository

_hasher = PasswordHasher()
# Verified against when the email is unknown, so response time doesn't reveal it
_DUMMY_HASH = _hasher.hash("dummy-password")


class AuthService:
    def __init__(self, repository: IdentityRepository) -> None:
        self.repository = repository

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(email)
        hash_to_check = user.password_hash if user and user.password_hash else _DUMMY_HASH

        try:
            _hasher.verify(hash_to_check, password)
        except (VerifyMismatchError, InvalidHashError):
            return None

        if user is None or not user.password_hash:
            return None  # unknown email or OAuth-only account
        return user
