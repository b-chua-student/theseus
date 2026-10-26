from uuid import UUID

from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class DeleteHistoryService:
    """Application service for deleting a manuscript's revision history."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to delete revision histories.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> None:
        """Delete the revision history for a manuscript.

        Args:
            manuscript_id: UUID of the manuscript whose history to delete.

        Raises:
            ValueError: If no history exists for the given manuscript.
        """
        if not self._repository.exists(manuscript_id):
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")
        self._repository.delete(manuscript_id)
