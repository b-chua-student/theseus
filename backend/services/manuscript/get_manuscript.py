from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class GetManuscriptService:
    """Application service for retrieving a manuscript by its identifier."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> Manuscript:
        """Retrieve a manuscript by its ID.

        Args:
            manuscript_id: Unique identifier of the manuscript.

        Returns:
            The matching manuscript.

        Raises:
            ValueError: If no manuscript with the given ID exists.
        """
        manuscript = self._repository.get_by_id(manuscript_id)
        if manuscript is None:
            raise ValueError(f"Manuscript '{manuscript_id}' not found.")
        return manuscript
