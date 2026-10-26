from uuid import UUID

from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class DeleteBranchService:
    """Application service for deleting a branch."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist revision histories.
        """
        self._repository = repository

    def execute(self, manuscript_id: UUID, branch_name: str) -> None:
        """Delete a branch from the revision history.

        Args:
            manuscript_id: UUID of the manuscript.
            branch_name: Name of the branch to delete.

        Raises:
            ValueError: If no history exists for the manuscript.
            InvalidRevisionError: If the branch is ``main``.
            BranchNotFoundError: If the branch does not exist.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        history.delete_branch(branch_name)
        self._repository.save(history)
