from uuid import UUID

from .value_objects import DisplayName, Email


class User:
    """Aggregate root for a user account."""

    def __init__(self, id: UUID, email: Email, display_name: DisplayName) -> None:
        """Create a user.

        Args:
            id: Unique identifier of the user.
            email: The user's email address.
            display_name: The user's display name.
        """
        self._id = id
        self._email = email
        self._display_name = display_name

    @property
    def id(self) -> UUID:
        """Unique identifier of the user."""
        return self._id

    @property
    def email(self) -> Email:
        """Current email address."""
        return self._email

    @property
    def display_name(self) -> DisplayName:
        """Current display name."""
        return self._display_name

    def rename(self, display_name: DisplayName) -> None:
        """Change the display name.

        Args:
            display_name: The new display name.
        """
        self._display_name = display_name

    def change_email(self, email: Email) -> None:
        """Change the email address.

        Args:
            email: The new email address.
        """
        self._email = email
