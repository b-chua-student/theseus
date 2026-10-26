from uuid import UUID

from repositories.user.user_repository import UserRepository


class DeleteUserService:
    """Application service for deleting a user."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist users.
        """
        self._repository = repository

    def execute(self, user_id: UUID) -> None:
        """Delete a user by its identifier.

        Args:
            user_id: Unique identifier of the user to delete.

        Raises:
            ValueError: If the user does not exist.
        """
        user = self._repository.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        self._repository.delete(user_id)
