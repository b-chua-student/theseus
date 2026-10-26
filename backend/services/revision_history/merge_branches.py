from uuid import UUID

from domain.revision_history.entities import Revision
from domain.revision_history.value_objects import CommitMessage, MergeConflict, Snapshot
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class MergeBranchesService:
    """Application service for merging two branches."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist revision histories.
        """
        self._repository = repository

    def execute(
        self,
        manuscript_id: UUID,
        source_branch_name: str,
        target_branch_name: str,
        tree_hash: str,
        message: str,
        conflicts: tuple[MergeConflict, ...] = (),
    ) -> Revision:
        """Merge the source branch into the target branch.

        Args:
            manuscript_id: UUID of the manuscript.
            source_branch_name: Name of the branch to merge from.
            target_branch_name: Name of the branch to merge into.
            tree_hash: Snapshot tree hash of the merged state.
            message: Commit message for the merge revision.
            conflicts: Unresolved merge conflicts, if any.

        Returns:
            The newly created merge revision.

        Raises:
            ValueError: If no history exists for the manuscript.
            InvalidRevisionError: If source and target are the same.
            BranchNotFoundError: If either branch does not exist.
            MergeConflictError: If unresolved conflicts are provided.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        revision = history.merge(
            source_branch_name=source_branch_name,
            target_branch_name=target_branch_name,
            snapshot=Snapshot(tree_hash=tree_hash),
            message=CommitMessage(value=message),
            conflicts=conflicts,
        )
        self._repository.save(history)
        return revision
