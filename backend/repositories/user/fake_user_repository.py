from uuid import UUID

from domain.user.aggregates import User
from domain.user.value_objects import DisplayName, Email
from repositories.user.user_repository import UserRepository


class FakeUserRepository(UserRepository):
    """In-memory user repository for development and testing.

    Attributes:
        OWNER_ID: Identifier of the seeded user; owns the seeded project.
    """

    OWNER_ID = UUID("00000000-0000-0000-0000-0000000000a1")

    def __init__(self, *, seed: bool = True) -> None:
        """Initialize the repository.

        Args:
            seed: If True, add the user that owns the seeded project.
        """
        self._users: dict[UUID, User] = {}

        if seed:
            self.save(
                User(
                    id=self.OWNER_ID,
                    email=Email("owner@example.com"),
                    display_name=DisplayName("Sample Owner"),
                )
            )

    def save(self, user: User) -> None:
        """Store a user, replacing any existing one with the same id.

        Args:
            user: The user to save.
        """
        self._users[user.id] = user

    def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by its identifier.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The matching user, or None if not found.
        """
        return self._users.get(user_id)

    def get_by_email(self, email: Email) -> User | None:
        """Retrieve a user by email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching user, or None if not found.
        """
        return next((u for u in self._users.values() if u.email == email), None)

    def delete(self, user_id: UUID) -> None:
        """Delete a user by its identifier.

        Does nothing if the user does not exist.

        Args:
            user_id: The unique identifier of the user.
        """
        self._users.pop(user_id, None)
