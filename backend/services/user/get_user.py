from uuid import UUID

from domain.user.aggregates import User
from repositories.user.user_repository import UserRepository


class GetUserService:
    """Application service for retrieving a single user by ID."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to retrieve users.
        """
        self._repository = repository

    def execute(self, user_id: UUID) -> User:
        """Fetch a user by its identifier.

        Args:
            user_id: Unique identifier of the user.

        Returns:
            The matching user.

        Raises:
            ValueError: If the user does not exist.
        """
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with ID {user_id} not found.")
        return user
