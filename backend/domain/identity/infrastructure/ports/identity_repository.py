from abc import ABC, abstractmethod

from domain.identity.models.aggregates import User
from domain.identity.models.value_objects import Email, UserId


class IdentityRepository(ABC):
    """Persistence contract for User aggregates."""

    @abstractmethod
    def add_user(self, user: User) -> User | None:
        """Store a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UserId) -> User | None:
        """Return the user with the given id, or None if not found."""
        pass

    @abstractmethod
    def get_by_ids(self, user_ids: list[UserId]) -> list[User]:
        """Return the users matching the given ids, or None if there are none."""
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """Return the user with the given email, or None if not found."""
        pass

    def find_identity(self, issuer: str, subject: str) -> User | None:
        """Load the account owning the external identity."""
        raise NotImplementedError

    def provision(self, user: User, issuer: str, subject: str) -> None:
        """Atomically insert the account and identity or raise IdentityConflict."""
        raise NotImplementedError

    def link(self, user: User, issuer: str, subject: str) -> None:
        """Attach the identity or raise IdentityConflict if owned elsewhere."""
        raise NotImplementedError

    def rename(self, user: User, name: str) -> None:
        """Persist the validated display name."""
        raise NotImplementedError


class IdentityConflict(Exception):
    """An account or external identity already owns a unique key."""
