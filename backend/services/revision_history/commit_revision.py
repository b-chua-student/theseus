from uuid import UUID

from domain.revision_history.entities import Revision
from domain.revision_history.value_objects import CommitMessage, Snapshot
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class CommitRevisionService:
    """Application service for committing a new revision on a branch."""

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
        tree_hash: str,
        message: str,
    ) -> Revision:
        """Commit a new revision on the given branch.

        Args:
            manuscript_id: UUID of the manuscript.
            branch_name: Name of the branch to commit to.
            tree_hash: Snapshot tree hash for the new revision.
            message: Commit message.

        Returns:
            The newly created revision.

        Raises:
            ValueError: If no history exists for the manuscript.
            BranchNotFoundError: If the branch does not exist.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        revision = history.commit(
            branch_name=branch_name,
            snapshot=Snapshot(tree_hash=tree_hash),
            message=CommitMessage(value=message),
        )
        self._repository.save(history)
        return revision
