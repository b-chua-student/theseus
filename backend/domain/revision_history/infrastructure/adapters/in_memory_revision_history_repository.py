from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import ConcurrentModificationError
from domain.revision_history.models.value_objects import ManuscriptId


class InMemoryRevisionHistoryRepository(RevisionHistoryRepository):
    """Non-persistent revision history repository backed by a dict, for tests."""

    def __init__(self) -> None:
        """Start with no stored histories or versions."""
        self._versions: dict[ManuscriptId, int] = {}
        self._db: dict[ManuscriptId, RevisionHistory] = {}

    def get_by_manuscript_id(self, manuscript_id: ManuscriptId) -> RevisionHistory | None:
        """Return the stored history if it exists."""
        return self._db.get(manuscript_id)

    def add(self, history: RevisionHistory) -> None:
        """Store a new history."""
        self.save(history)

    def save(self, history: RevisionHistory) -> None:
        """Store the history and advance its version if it is current."""
        if self._versions.get(history.manuscript_id, 0) != history.version:
            raise ConcurrentModificationError("History changed during the operation.")
        history.version += 1
        self._versions[history.manuscript_id] = history.version
        self._db[history.manuscript_id] = history
