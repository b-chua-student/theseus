from uuid import uuid4

from domain.user.aggregates import User
from domain.user.value_objects import DisplayName, Email
from repositories.user.user_repository import UserRepository


class CreateUserService:
    """Application service for creating a new user."""

    def __init__(self, repository: UserRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist users.
        """
        self._repository = repository

    def execute(self, email: str, display_name: str) -> User:
        """Create and persist a user.

        Args:
            email: Email address of the new user.
            display_name: Display name of the new user.

        Returns:
            The newly created user.

        Raises:
            ValueError: If the email or display name is invalid, or the email
                is already registered.
        """
        email_vo = Email(email)
        if self._repository.get_by_email(email_vo) is not None:
            raise ValueError(f"A user with email '{email_vo.value}' already exists.")

        user = User(
            id=uuid4(),
            email=email_vo,
            display_name=DisplayName(display_name),
        )
        self._repository.save(user)
        return user
