from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class CreateManuscriptService:
    """Application service for creating a new manuscript within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(
        self,
        project_id: UUID,
        title: str,
    ) -> Manuscript:
        """Create docstring."""
        # TODO: Generate manuscript ID.
        # TODO: Build Manuscript aggregate.
        # TODO: Persist manuscript.
        # TODO: Return created manuscript.
        raise NotImplementedError
