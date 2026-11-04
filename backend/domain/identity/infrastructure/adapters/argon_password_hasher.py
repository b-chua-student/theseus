from argon2 import PasswordHasher as _Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from domain.identity.infrastructure.ports.password_hasher import PasswordHasher


class ArgonPasswordHasher(PasswordHasher):
    """Argon2-based password hasher."""

    def __init__(self, time_cost: int = 3, memory_cost: int = 65536, parallelism: int = 4) -> None:
        self._hasher = _Argon2Hasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )

    def hash(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def needs_rehash(self, hashed: str) -> bool:
        return self._hasher.check_needs_rehash(hashed)
