from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.value_objects import ManuscriptId, Snapshot


class GetCurrentContentService:
    """Content of a manuscript = snapshot of the current draft's latest revision.

    Returns None when the manuscript has no revision history yet.
    """

    def __init__(self, repository: RevisionHistoryRepository) -> None:
        self._repository = repository

    def execute(self, manuscript_id: str) -> Snapshot | None:
        """Return the current draft's head snapshot, or None if no history exists."""
        history = self._repository.get_by_manuscript_id(ManuscriptId.from_str(manuscript_id))
        if history is None:
            return None
        return history.current_draft.head.snapshot
