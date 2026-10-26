from uuid import UUID

from domain.revision_history.entities import Milestone
from repositories.revision_history.revision_history_repository import RevisionHistoryRepository


class AddMilestoneService:
    """Application service for adding a milestone to a revision history."""

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
        revision_id: UUID,
    ) -> Milestone:
        """Add a named milestone pointing to a revision.

        Args:
            manuscript_id: UUID of the manuscript.
            name: Name of the milestone.
            revision_id: UUID of the revision to associate with the milestone.

        Returns:
            The newly created milestone.

        Raises:
            ValueError: If no history exists for the manuscript.
            DuplicateMilestoneError: If the milestone name is already taken.
            RevisionNotFoundError: If the revision does not exist.
        """
        history = self._repository.get_by_manuscript_id(manuscript_id)
        if history is None:
            raise ValueError(f"Revision history not found for manuscript: {manuscript_id}")

        milestone = history.add_milestone(name=name, revision_id=revision_id)
        self._repository.save(history)
        return milestone
