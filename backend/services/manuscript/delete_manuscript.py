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
        """Delete an existing manuscript by its unique identifier.

        Args:
            manuscript_id: The unique identifier of the manuscript to delete.

        Raises:
            ValueError: If no manuscript exists with the given identifier.
        """
        manuscript = self._repository.get_by_id(manuscript_id)
        if manuscript is None:
            raise ValueError(f"Manuscript with ID {manuscript_id} not found.")

        self._repository.delete(manuscript_id)
