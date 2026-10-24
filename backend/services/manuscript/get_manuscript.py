from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetManuscriptService:
    """Application service for retrieving a manuscript within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> Manuscript:
        """Create docstring."""
        # TODO: Load manuscript by ID.
        # TODO: Raise not-found error if missing.
        # TODO: Return manuscript.
        raise NotImplementedError
