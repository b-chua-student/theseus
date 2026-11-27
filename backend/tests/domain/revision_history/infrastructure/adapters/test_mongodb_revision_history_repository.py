from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pymongo.database import Database
from pymongo.results import UpdateResult

from domain.revision_history.infrastructure.adapters.mongodb_revision_history_repository import (
    MongoRevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import ConcurrentModificationError
from domain.revision_history.models.value_objects import ManuscriptId, SectionSnapshot, Snapshot


@pytest.fixture
def mongo_context() -> tuple[MongoRevisionHistoryRepository, MagicMock, MagicMock]:
    database = MagicMock(spec=Database)
    histories, revisions = MagicMock(), MagicMock()
    database.__getitem__.side_effect = {
        "revision_histories": histories,
        "revisions": revisions,
    }.__getitem__
    return MongoRevisionHistoryRepository(database), histories, revisions


def test_history_round_trip_preserves_shared_ordered_revisions_and_merge_source(
    mongo_context: tuple[MongoRevisionHistoryRepository, MagicMock, MagicMock],
) -> None:
    repository, histories, revisions = mongo_context
    history = RevisionHistory.start(ManuscriptId.new(), Snapshot(()))
    initial = history.current_draft.head
    history.create_branch("review")
    snapshot = Snapshot((SectionSnapshot(uuid4(), None, "Results", 0, "Reviewed findings"),))
    source = history.commit("review", snapshot, "Review findings")
    merged = history.plan_merge("main", "review")
    history.attach("main", merged)
    history.switch_draft("review")
    histories.replace_one.return_value = UpdateResult(
        {"n": 1, "nModified": 0, "upserted": str(history.manuscript_id.value)}, acknowledged=True
    )

    repository.add(history)

    [documents] = revisions.insert_many.call_args.args
    assert {doc["_id"] for doc in documents} == {str(r.id.value) for r in (initial, source, merged)}
    assert len(documents) == 3
    histories.find_one.return_value = histories.replace_one.call_args.args[1]
    revisions.find.return_value = list(reversed(documents))

    loaded = repository.get_by_manuscript_id(history.manuscript_id)

    assert loaded is not None
    assert loaded.version == 1
    assert loaded.current_draft.name == "review"
    assert loaded.current_draft.revisions == [initial, source]
    assert loaded.get_branch("main").revisions == [initial, merged]
    assert loaded.get_branch("main").head.merged_from == merged.merged_from


@pytest.mark.parametrize("matched", [False, True], ids=["stale", "saved"])
def test_orphans_are_deleted_only_after_history_write_matches(
    mongo_context: tuple[MongoRevisionHistoryRepository, MagicMock, MagicMock], *, matched: bool
) -> None:
    repository, histories, revisions = mongo_context
    history = RevisionHistory.start(ManuscriptId.new(), Snapshot(()))
    history.version = 2
    retained_id = str(history.current_draft.head.id.value)
    orphaned_id = str(uuid4())
    revisions.find.return_value = [{"_id": retained_id}, {"_id": orphaned_id}]
    histories.replace_one.return_value = UpdateResult({"n": int(matched)}, acknowledged=True)

    if matched:
        repository.save(history)
        assert history.version == 3
        revisions.delete_many.assert_called_once_with({"_id": {"$in": [orphaned_id]}})
    else:
        with pytest.raises(ConcurrentModificationError):
            repository.save(history)
        assert history.version == 2
        revisions.delete_many.assert_not_called()

    assert histories.replace_one.call_args.args[0] == {
        "_id": str(history.manuscript_id.value),
        "version": 2,
    }
    revisions.insert_many.assert_not_called()
