from dataclasses import replace
from typing import Literal
from uuid import uuid4

import pytest

from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import MergeConflictError, NoChangesError, RevisionError
from domain.revision_history.models.merge import Resolution
from domain.revision_history.models.value_objects import (
    ManuscriptId,
    MergeSource,
    SectionSnapshot,
    Snapshot,
)


def test_branch_from_an_earlier_revision_preserves_main_history() -> None:
    initial = Snapshot(())
    history = RevisionHistory.start(ManuscriptId.new(), initial)
    first = history.current_draft.head
    updated = Snapshot((SectionSnapshot(uuid4(), None, "Results", 1, ""),))
    latest = history.commit("main", updated, "Add results")

    draft = history.create_branch("experiment", from_revision_id=first.id)
    assert draft.revisions == [first]
    assert history.current_draft.head == latest
    with pytest.raises(NoChangesError):
        history.commit("experiment", initial, "Unchanged")

    restored = history.restore("main", first.id)
    assert restored.id != first.id
    assert restored.snapshot == initial
    assert history.get_branch("main").revisions == [first, latest, restored]


def test_current_draft_keeps_its_status_when_renamed() -> None:
    history = RevisionHistory.start(ManuscriptId.new(), Snapshot(()))
    history.create_branch("experiment")
    history.switch_draft("experiment")
    history.rename_draft("experiment", "review")

    assert history.current_draft.name == "review"
    with pytest.raises(RevisionError, match="current draft cannot be deleted"):
        history.delete_draft("review")
    with pytest.raises(RevisionError, match="main draft cannot be renamed"):
        history.rename_draft("main", "original")
    history.switch_draft("main")
    history.delete_draft("review")
    assert [branch.name for branch in history.branches] == ["main"]


def test_merge_conflict_can_be_resolved_with_source_body() -> None:
    section = SectionSnapshot(uuid4(), None, "Results", 0, "Initial")
    history = RevisionHistory.start(ManuscriptId.new(), Snapshot((section,)))
    history.create_branch("review")
    target = history.commit("main", Snapshot((replace(section, body="Main"),)), "Edit main")
    source = history.commit("review", Snapshot((replace(section, body="Review"),)), "Edit review")

    with pytest.raises(MergeConflictError) as error:
        history.plan_merge("main", "review")
    assert [(item.section_id, item.field) for item in error.value.conflicts] == [
        (section.id, "body")
    ]
    assert history.current_draft.head == target

    merged = history.plan_merge("main", "review", [Resolution(section.id, "body", "source")])
    assert merged.snapshot == source.snapshot
    assert merged.merged_from == MergeSource("review", source.id)
    history.attach("main", merged)
    assert history.find_merge_base("main", "review") == source


@pytest.mark.parametrize("choice", ["target", "source"])
def test_merge_resolves_deletion_of_a_nested_section_edited_in_the_other_draft(
    choice: Literal["target", "source"],
) -> None:
    parent = SectionSnapshot(uuid4(), None, "Methods", 0, "")
    child = SectionSnapshot(uuid4(), parent.id, "Sampling", 0, "Original method")
    history = RevisionHistory.start(ManuscriptId.new(), Snapshot((parent, child)))
    history.create_branch("review")
    history.commit("main", Snapshot((parent,)), "Remove sampling")
    edited = replace(child, body="Updated method")
    history.commit("review", Snapshot((parent, edited)), "Revise sampling")

    with pytest.raises(MergeConflictError) as error:
        history.plan_merge("main", "review")
    [conflict] = error.value.conflicts
    assert (conflict.section_id, conflict.field, conflict.kind) == (
        child.id,
        "section",
        "deleted_in_target",
    )

    if choice == "target":
        with pytest.raises(NoChangesError):
            history.plan_merge("main", "review", [Resolution(child.id, "section", choice)])
    else:
        merged = history.plan_merge("main", "review", [Resolution(child.id, "section", choice)])
        assert merged.snapshot.sections == (parent, edited)
