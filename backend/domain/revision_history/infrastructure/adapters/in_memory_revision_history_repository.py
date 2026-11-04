from domain.revision_history.infrastructure.ports.revision_history_repository import (
    RevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.value_objects import ManuscriptId


class InMemoryRevisionHistoryRepository(RevisionHistoryRepository):
    """Non-persistent revision history repository backed by a dict, for tests."""

    def __init__(self) -> None:
        self._db: dict[ManuscriptId, RevisionHistory] = {}

    def get_by_manuscript_id(self, manuscript_id: ManuscriptId) -> RevisionHistory | None:
        return self._db.get(manuscript_id)

    def add(self, history: RevisionHistory) -> None:
        self._db[history.manuscript_id] = history

    def save(self, history: RevisionHistory) -> None:
        self._db[history.manuscript_id] = history
