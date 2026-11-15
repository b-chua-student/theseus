from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory
from repositories.revision_history.revision_history_repository import (
    RevisionHistoryRepository,
)


class FakeRevisionHistoryRepository(RevisionHistoryRepository):
    """In-memory revision history repository for development and testing.

    Stores revision history aggregates keyed by manuscript identifier.

    Attributes:
        PROJECT_ID: Project identifier assigned to seeded revision histories.
    """

    PROJECT_ID = UUID("00000000-0000-0000-0000-000000000001")

    def __init__(self, *, seed: bool = True) -> None:
        """Initialize the repository.

        Args:
            seed: If True, populate the repository with sample revision
                histories.
        """
        self._revision_histories: dict[UUID, RevisionHistory] = {}

        if seed:
            self._seed()

    def _seed(self) -> None:
        """Populate the repository with sample revision histories.

        Creates revision histories for sample manuscripts. Each history is
        initialized with an initial revision and a main branch.
        """
        # Add sample revision histories here when suitable sample snapshots
        # and commit messages are available.
        pass

    def save(self, revision_history: RevisionHistory) -> None:
        """Store a revision history, replacing any existing one.

        Revision histories are keyed by manuscript identifier, ensuring
        that each manuscript has at most one revision history.

        Args:
            revision_history: The revision history aggregate to save.
        """
        self._revision_histories[revision_history.manuscript_id] = revision_history

    def get_by_manuscript_id(
        self,
        manuscript_id: UUID,
    ) -> RevisionHistory | None:
        """Retrieve a revision history by its manuscript identifier.

        Args:
            manuscript_id: UUID of the manuscript associated with the
                revision history.

        Returns:
            The matching revision history, or None if not found.
        """
        return self._revision_histories.get(manuscript_id)

    def get_by_project_id(self, project_id: UUID) -> list[RevisionHistory]:
        """Retrieve all revision histories belonging to a project.

        Args:
            project_id: UUID of the project.

        Returns:
            A list of matching revision histories, empty if none exist.
        """
        return [
            revision_history
            for revision_history in self._revision_histories.values()
            if revision_history.project_id == project_id
        ]

    def get_all(self) -> list[RevisionHistory]:
        """Retrieve all stored revision histories.

        Returns:
            A list of all revision histories, empty if none exist.
        """
        return list(self._revision_histories.values())

    def delete(self, manuscript_id: UUID) -> None:
        """Delete a revision history by its manuscript identifier.

        Does nothing if the revision history does not exist.

        Args:
            manuscript_id: UUID of the manuscript associated with the
                revision history.
        """
        self._revision_histories.pop(manuscript_id, None)

    def exists(self, manuscript_id: UUID) -> bool:
        """Check whether a revision history exists for a manuscript.

        Args:
            manuscript_id: UUID of the manuscript.

        Returns:
            True if a revision history exists, otherwise False.
        """
        return manuscript_id in self._revision_histories

    def clear(self) -> None:
        """Remove all revision histories from the repository."""
        self._revision_histories.clear()
