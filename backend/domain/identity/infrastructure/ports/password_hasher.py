from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Contract for hashing and verifying passwords."""

    @abstractmethod
    def hash(self, plain: str) -> str:
        """Return a salted hash of the plain-text password."""
        pass

    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool:
        """Return True if the plain-text password matches the hash."""
        pass
