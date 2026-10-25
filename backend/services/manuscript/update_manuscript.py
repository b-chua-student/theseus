from uuid import UUID

from domain.manuscript.aggregates import Manuscript
from repositories.manuscript.manuscript_repository import ManuscriptRepository


class UpdateManuscriptService:
    """Application service for updating a manuscript within a project."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist manuscripts.
        """
        self._repository = repository

    def execute(
        self,
        manuscript_id: UUID,
        title: str,
    ) -> Manuscript:
        """Update a manuscript title by ID."""

        manuscript = self._repository.get_by_id(manuscript_id)

        if manuscript is None:
            raise ValueError("Manuscript not found.")

        manuscript.rename(title)
        self._repository.save(manuscript)

        return manuscript
