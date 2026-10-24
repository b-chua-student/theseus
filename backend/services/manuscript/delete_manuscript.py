from uuid import UUID

from repositories.manuscript.manuscript_repository import ManuscriptRepository


class DeleteManuscriptService:
    """Application service for deleting a manuscript within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> None:
        """Create docstring."""
        # TODO: Load manuscript by ID.
        # TODO: Raise not-found error if missing.
        # TODO: Delete manuscript.
        raise NotImplementedError
