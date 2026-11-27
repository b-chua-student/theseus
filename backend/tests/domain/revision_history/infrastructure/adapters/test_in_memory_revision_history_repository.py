import pytest

from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import ConcurrentModificationError
from domain.revision_history.models.value_objects import ManuscriptId, Snapshot


def test_repository_rejects_a_stale_write() -> None:
    repository = InMemoryRevisionHistoryRepository()
    manuscript_id = ManuscriptId.new()
    history = RevisionHistory.start(manuscript_id, Snapshot(()))
    stale = RevisionHistory.start(manuscript_id, Snapshot(()))

    assert repository.get_by_manuscript_id(manuscript_id) is None
    repository.add(history)
    history.create_branch("review")
    repository.save(history)

    with pytest.raises(ConcurrentModificationError):
        repository.save(stale)
    stored = repository.get_by_manuscript_id(manuscript_id)
    assert stored is not None
    assert stored.get_branch("review").head == history.get_branch("main").head
