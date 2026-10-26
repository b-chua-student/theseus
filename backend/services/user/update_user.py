from uuid import UUID

from domain.user.aggregates import User
from domain.user.value_objects import DisplayName, Email
from repositories.user.user_repository import UserRepository


class UpdateUserService:
    """Application service for updating a user's email and/or display name."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist users.
        """
        self._repository = repository

    def execute(
        self,
        user_id: UUID,
        *,
        display_name: str | None = None,
        email: str | None = None,
    ) -> User:
        """Update a user's fields and persist the changes.

        At least one of ``display_name`` or ``email`` must be provided.

        Args:
            user_id: Unique identifier of the user to update.
            display_name: New display name, or None to leave unchanged.
            email: New email address, or None to leave unchanged.

        Returns:
            The updated user aggregate.

        Raises:
            ValueError: If the user is not found, no fields are provided,
                the new values are invalid, or the email is already taken
                by another user.
        """
        if display_name is None and email is None:
            raise ValueError("At least one of 'display_name' or 'email' must be provided.")

        user = self._repository.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        if email is not None:
            new_email = Email(email)
            existing = self._repository.get_by_email(new_email)
            if existing is not None and existing.id != user_id:
                raise ValueError(f"A user with email '{new_email.value}' already exists.")
            user.change_email(new_email)

        if display_name is not None:
            user.rename(DisplayName(display_name))

        self._repository.save(user)
        return user
