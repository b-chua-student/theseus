from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class GetHistoryService:
    """Application service for retrieving a manuscript's revision history."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to fetch revision histories.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID) -> RevisionHistory:
        """Retrieve the revision history for a manuscript.

        Args:
            manuscript_id: UUID of the manuscript.

        Returns:
            The revision history for the manuscript.

        Raises:
            ValueError: If no history exists for the given manuscript.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")
        return history
