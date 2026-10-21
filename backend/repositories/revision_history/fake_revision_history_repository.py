from uuid import UUID

from domain.revision_history.aggregates import RevisionHistory
from .revision_history_repository import RevisionHistoryRepository


class FakeRevisionHistoryRepository(RevisionHistoryRepository):
    def __init__(self) -> None:
        self._histories: dict[UUID, RevisionHistory] = {}

    def save(self, history: RevisionHistory) -> None:
        self._histories[history.manuscript_id] = history

    def get_by_manuscript_id(
        self,
        manuscript_id: UUID,
    ) -> RevisionHistory | None:
        return self._histories.get(manuscript_id)

    def delete(self, manuscript_id: UUID) -> None:
        self._histories.pop(manuscript_id, None)
