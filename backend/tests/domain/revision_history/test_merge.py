from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from uuid import UUID

import pytest
from flask import Flask
from hypothesis import given, settings
from hypothesis import strategies as st

from bootstrap.error_handlers import register_error_handlers
from domain.revision_history.api.routes import draft_bp
from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import (
    ConcurrentModificationError,
    InvalidResolutionError,
    MergeConflictError,
    MergeInProgressError,
    NoChangesError,
    UnsavedChangesError,
)
from domain.revision_history.models.merge import (
    Conflicts,
    Merged,
    Resolution,
    merge_snapshots,
    normalize,
)
from domain.revision_history.models.value_objects import ManuscriptId, SectionSnapshot, Snapshot
from domain.revision_history.services.merge_draft import MergeDraftService, MergeLocks


def section(n=1, **kwargs):
    return replace(SectionSnapshot(UUID(int=n), None, "Heading", 0, "base"), **kwargs)


def snap(*sections):
    return Snapshot(tuple(sections))


def setup_merge(conflict=False):
    base = snap(section())
    history = RevisionHistory.start(ManuscriptId.new(), base)
    history.create_branch("feature")
    history.commit("feature", snap(section(body="source")), "source")
    if conflict:
        history.commit("main", snap(section(body="target")), "target")
    repo = InMemoryRevisionHistoryRepository()
    repo.add(history)

    class Working:
        snapshot = history.current_draft.head.snapshot

        def get_snapshot(self, key):
            return self.snapshot

        def apply_snapshot(self, key, snapshot):
            self.snapshot = snapshot

    working = Working()
    service = MergeDraftService(repo, working, working, MergeLocks())
    return history, repo, working, service


# Feature: merge-drafts, Property 1: Field-level merge rule
@settings(max_examples=100)
@given(st.text(), st.text(), st.text())
def test_req_3_1_to_3_8_and_4_1_field_rule(base, target, source):
    result = merge_snapshots(
        snap(section(body=base)), snap(section(body=target)), snap(section(body=source))
    )
    if target != source and target != base and source != base:
        assert isinstance(result, Conflicts)
        assert result.conflicts[0].field == "body"
    else:
        assert isinstance(result, Merged)
        assert result.snapshot.sections[0].body == (source if target == base else target)


# Feature: merge-drafts, Property 2: Merged snapshot is well formed
# Feature: merge-drafts, Property 4: Fast-forward
@settings(max_examples=100)
@given(st.lists(st.text(), min_size=1, max_size=20))
def test_req_3_9_3_12_3_13_10_3_wellformed_fast_forward(bodies):
    base = snap(section())
    source = snap(*(section(i + 1, body=body, ordinal=i * 3) for i, body in enumerate(bodies)))
    result = merge_snapshots(base, base, source)
    assert isinstance(result, Merged)
    assert result.snapshot == normalize(source)
    assert len({s.id for s in result.snapshot.sections}) == len(bodies)
    assert [s.ordinal for s in result.snapshot.sections] == list(range(len(bodies)))
    assert all(s.parent_id is None for s in result.snapshot.sections)
    assert merge_snapshots(source, source, source).snapshot == normalize(source)


# Feature: merge-drafts, Property 3: Merging a draft with no new changes is rejected
@settings(max_examples=100)
@given(st.text())
def test_req_3_10_10_2_identity(body):
    history = RevisionHistory.start(ManuscriptId.new(), snap(section(body=body)))
    history.create_branch("copy")
    with pytest.raises(NoChangesError):
        history.plan_merge("main", "copy")


def test_req_4_2_5_3_5_4_delete_keep_descendants():
    base = snap(section(), section(2, parent_id=UUID(int=1)))
    source = snap(section(body="changed"), section(2, parent_id=UUID(int=1), body="child"))
    assert isinstance(merge_snapshots(base, snap(), source), Conflicts)
    keep = merge_snapshots(base, snap(), source, [Resolution(UUID(int=1), "section", "source")])
    assert keep.snapshot == normalize(source)
    delete = merge_snapshots(base, snap(), source, [Resolution(UUID(int=1), "section", "target")])
    assert delete.snapshot == snap()


def test_req_4_3_4_4_5_9_structural_conflicts():
    base = snap(section(), section(2))
    target = snap(section(parent_id=UUID(int=2)), section(2))
    source = snap(section(), section(2, parent_id=UUID(int=1)))
    result = merge_snapshots(base, target, source)
    assert isinstance(result, Conflicts)
    assert result.conflicts[0].kind == "parent_cycle"
    result = merge_snapshots(base, target, source, [Resolution(UUID(int=2), "parent_id", "target")])
    assert isinstance(result, Merged)
    missing = merge_snapshots(
        base, snap(section()), snap(section(), section(2, body="changed", parent_id=UUID(int=3)))
    )
    assert isinstance(missing, Conflicts)


def test_req_2_3_2_4_repeat_merge_after_rename():
    history, repo, working, service = setup_merge()
    branch = service.execute(str(history.manuscript_id.value), "feature")
    assert branch.head.merged_from.head_revision_id == history.get_branch("feature").head.id
    history.rename_draft("feature", "renamed")
    with pytest.raises(NoChangesError):
        service.execute(str(history.manuscript_id.value), "renamed")
    history.commit("renamed", snap(section(body="next")), "next")
    service.execute(str(history.manuscript_id.value), "renamed")
    assert working.snapshot.sections[0].body == "next"


def test_req_6_3_10_4_conflict_changes_nothing_and_resolution():
    history, repo, working, service = setup_merge(True)
    before = deepcopy(history.current_draft.revisions), working.snapshot
    with pytest.raises(MergeConflictError):
        service.execute(str(history.manuscript_id.value), "feature")
    assert (history.current_draft.revisions, working.snapshot) == before
    service.execute(
        str(history.manuscript_id.value), "feature", [Resolution(UUID(int=1), "body", "source")]
    )
    assert working.snapshot.sections[0].body == "source"


def test_req_5_6_5_7_6_1_invalid_and_dirty():
    history, repo, working, service = setup_merge(True)
    key = str(history.manuscript_id.value)
    with pytest.raises(InvalidResolutionError):
        service.execute(key, "feature", [Resolution(UUID(int=1), "heading", "source")])
    working.snapshot = snap(section(body="unsaved"))
    with pytest.raises(UnsavedChangesError):
        service.execute(key, "feature")


def test_req_6_3_save_failure_rolls_back():
    history, repo, working, service = setup_merge()
    before = list(history.current_draft.revisions), working.snapshot

    def fail(history):
        raise RuntimeError("save failed")

    repo.save = fail
    with pytest.raises(RuntimeError):
        service.execute(str(history.manuscript_id.value), "feature")
    assert (history.current_draft.revisions, working.snapshot) == before


def test_req_6_4_version_and_lock():
    history, repo, working, service = setup_merge()
    stale = deepcopy(history)
    repo.save(history)
    with pytest.raises(ConcurrentModificationError):
        repo.save(stale)
    key = str(history.manuscript_id.value)
    with service._locks.try_acquire(key), pytest.raises(MergeInProgressError):
        service.execute(key, "feature")


@pytest.mark.parametrize(
    "body,status",
    [
        ({}, 200),
        ({"message": ""}, 422),
        (
            {
                "resolutions": [
                    {"section_id": str(UUID(int=1)), "field": "body", "choice": "invalid"}
                ]
            },
            422,
        ),
    ],
)
def test_req_7_2_7_3_10_5_api(body, status):
    history, repo, working, service = setup_merge()
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(draft_bp, url_prefix="/drafts")
    app.url_value_preprocessor(
        lambda endpoint, values: values.update(
            project_id="p", manuscript_id=str(history.manuscript_id.value)
        )
    )
    app.extensions["container"] = SimpleNamespace(
        revision_history=SimpleNamespace(merge_draft=service)
    )
    register_error_handlers(app)
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = "user"
    assert client.post("/drafts/feature/merge", json=body).status_code == status
    if status == 200:
        assert client.post("/drafts/feature/merge", json={}).status_code == 409
        assert client.post("/drafts/missing/merge", json={}).status_code == 404


def test_writer_emits_once_for_changed_snapshot():
    from unittest.mock import Mock

    from domain.manuscript.models.aggregates import Manuscript
    from domain.manuscript.models.events import ManuscriptContentReplaced
    from domain.manuscript.models.value_objects import ManuscriptTitle, ProjectId
    from domain.revision_history.infrastructure.adapters.manuscript_repository_writer import (
        ManuscriptRepositoryWriter,
    )

    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Test"), template=False)
    repo, publisher = Mock(), Mock()
    repo.get_by_id.return_value = manuscript
    writer = ManuscriptRepositoryWriter(repo, publisher)
    writer.apply_snapshot(str(manuscript.id.value), snap(section()))
    assert isinstance(publisher.publish.call_args.args[0][0], ManuscriptContentReplaced)
    writer.apply_snapshot(str(manuscript.id.value), snap(section()))
    assert publisher.publish.call_count == repo.save.call_count == 1


def test_mongo_provenance_and_legacy_roundtrip():
    from domain.revision_history.infrastructure.adapters import (
        mongodb_revision_history_repository,
    )

    MongoRevisionHistoryRepository = (
        mongodb_revision_history_repository.MongoRevisionHistoryRepository
    )

    history, repo, working, service = setup_merge()
    revision = service.execute(str(history.manuscript_id.value), "feature").head
    document = MongoRevisionHistoryRepository._revision_to_doc(
        str(history.manuscript_id.value), revision
    )
    assert MongoRevisionHistoryRepository._revision_from_doc(document) == revision
    del document["merged_from"]
    assert MongoRevisionHistoryRepository._revision_from_doc(document).merged_from is None


def test_parent_delete_dominates_child_keep():
    base = snap(section(), section(2, parent_id=UUID(int=1)))
    source = snap(section(body="changed"), section(2, parent_id=UUID(int=1), body="child"))
    result = merge_snapshots(
        base,
        snap(),
        source,
        [
            Resolution(UUID(int=1), "section", "target"),
            Resolution(UUID(int=2), "section", "source"),
        ],
    )
    assert result.snapshot == snap()
