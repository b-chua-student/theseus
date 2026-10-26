from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory
from domain.revision_history.value_objects import CommitMessage, Snapshot
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class InitializeHistoryService:
    """Application service for initializing a manuscript's revision history."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist revision histories.
        """
        self._repository = repository

    def execute(
        self,
        project_id: UUID,
        manuscript_id: UUID,
        tree_hash: str,
        message: str,
    ) -> RevisionHistory:
        """Create and initialize a new revision history for a manuscript.

        Args:
            project_id: UUID of the project that owns the manuscript.
            manuscript_id: UUID of the manuscript.
            tree_hash: Snapshot tree hash representing the initial state.
            message: Commit message for the initial revision.

        Returns:
            The newly created and initialized revision history.

        Raises:
            ValueError: If a history already exists for the manuscript.
            InvalidRevisionError: Should not occur on a fresh history.
        """
        if self._repository.exists(manuscript_id):
            raise ValueError(f"Revision history already exists for manuscript: {manuscript_id}")

        history = RevisionHistory(project_id=project_id, manuscript_id=manuscript_id)
        history.initialize(
            snapshot=Snapshot(tree_hash=tree_hash),
            message=CommitMessage(value=message),
        )
        self._repository.save(history)
        return history
