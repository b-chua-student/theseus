from uuid import UUID

from domain.revision_history.entities import Revision
from domain.revision_history.value_objects import CommitMessage
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class RestoreRevisionService:
    """Application service for restoring a previous revision on a branch."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist revision histories.
        """
        self._repository = repository

    def execute(
        self,
        manuscript_id: UUID,
        branch_name: str,
        target_revision_id: UUID,
        message: str,
    ) -> Revision:
        """Restore a previous revision's snapshot as a new commit on a branch.

        Args:
            manuscript_id: UUID of the manuscript.
            branch_name: Name of the branch to restore on.
            target_revision_id: UUID of the revision to restore from.
            message: Commit message for the restore revision.

        Returns:
            The newly created revision containing the restored snapshot.

        Raises:
            ValueError: If no history exists for the manuscript.
            BranchNotFoundError: If the branch does not exist.
            RevisionNotFoundError: If the target revision does not exist.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        revision = history.restore(
            branch_name=branch_name,
            target_revision_id=target_revision_id,
            message=CommitMessage(value=message),
        )
        self._repository.save(history)
        return revision
