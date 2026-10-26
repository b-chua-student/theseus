from uuid import UUID

from domain.revision_history.entities import Branch
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class CreateBranchService:
    """Application service for creating a new branch."""

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to persist revision histories.
        """
        self._repository = repository

    def execute(
        self,
        manuscript_id: UUID,
        name: str,
        from_revision_id: UUID | None = None,
    ) -> Branch:
        """Create a new branch in the revision history.

        Args:
            manuscript_id: UUID of the manuscript.
            name: Name of the new branch.
            from_revision_id: UUID of the revision to start the branch from.
                Defaults to the head of ``main``.

        Returns:
            A copy of the newly created branch.

        Raises:
            ValueError: If no history exists for the manuscript.
            DuplicateBranchError: If the branch name is already taken.
            InvalidRevisionError: If the history is not initialized.
            BranchNotFoundError: If ``main`` is missing and no revision given.
            RevisionNotFoundError: If ``from_revision_id`` does not exist.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        branch = history.create_branch(name=name, from_revision_id=from_revision_id)
        self._repository.save(history)
        return branch
