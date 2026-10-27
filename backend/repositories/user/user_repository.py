from abc import ABC, abstractmethod
from uuid import UUID

from domain.user.aggregates import User
from domain.user.value_objects import Email


class UserRepository(ABC):
    """Abstract repository for persisting and retrieving users."""

    @abstractmethod
    def save(self, user: User) -> None:
        """Persist a user, creating or updating it.

        Args:
            user: The user to save.
        """

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by its identifier.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The matching user, or None if not found.
        """

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching user, or None if not found.
        """

    @abstractmethod
    def delete(self, user_id: UUID) -> None:
        """Delete a user by its identifier.

        Args:
            user_id: The unique identifier of the user.
        """
