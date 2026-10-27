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
<<<<<<< HEAD
        """Update a manuscript title by ID."""

        manuscript = self._repository.get_by_id(manuscript_id)

        if manuscript is None:
            raise ValueError("Manuscript not found.")
=======
        """Rename an existing manuscript and persist the changes.

        Args:
            manuscript_id: Unique identifier of the manuscript to update.
            title: New title for the manuscript.

        Returns:
            The updated manuscript aggregate.

        Raises:
            ValueError: If the manuscript is not found or the title is invalid.
        """
        manuscript = self._repository.get_by_id(manuscript_id)
        if manuscript is None:
            raise ValueError(f"Manuscript with ID {manuscript_id} not found.")
>>>>>>> 3c7863b63299bddfdac8e69f9febe596134b93cf

        manuscript.rename(title)
        self._repository.save(manuscript)

        return manuscript
