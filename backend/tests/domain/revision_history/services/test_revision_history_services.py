import pytest

from bootstrap.contexts.manuscript.module import build_manuscript_module
from bootstrap.contexts.revision_history.module import RevisionHistoryModule
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.value_objects import ProjectId
from domain.revision_history.infrastructure.adapters.in_memory_revision_history_repository import (
    InMemoryRevisionHistoryRepository,
)
from domain.revision_history.models.aggregates import RevisionHistory
from domain.revision_history.models.errors import (
    ConcurrentModificationError,
    NoChangesError,
    UnsavedChangesError,
)
from domain.revision_history.models.value_objects import MergeSource
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus

pytestmark = pytest.mark.integration


def test_merge_rejects_unsaved_content_then_applies_committed_draft(
    history_services: RevisionHistoryModule,
    manuscript_repository: InMemoryManuscriptRepository,
    publisher: InProcessEventBus,
) -> None:
    manuscripts = build_manuscript_module(manuscript_repository, publisher)
    manuscript = manuscripts.create.execute(str(ProjectId.new().value), "Thesis", template=False)
    manuscript_id = str(manuscript.id.value)
    manuscripts.append_section.execute(manuscript_id, None, "Results")
    working = manuscripts.get.execute(manuscript_id)
    assert working is not None
    section_id = str(working.sections[0].id.value)

    history_services.start.execute(manuscript_id)
    initial = history_services.list.execute(manuscript_id)[0]
    history_services.start.execute(manuscript_id)
    assert history_services.list.execute(manuscript_id) == [initial]
    with pytest.raises(NoChangesError):
        history_services.commit.execute(manuscript_id, None, "Unchanged")

    history_services.create_draft.execute(manuscript_id, "review")
    history_services.switch_draft.execute(manuscript_id, "review")
    manuscripts.edit_section_body.execute(manuscript_id, section_id, "Reviewed findings")
    source = history_services.commit.execute(manuscript_id, None, "Review findings")
    history_services.switch_draft.execute(manuscript_id, "main")

    manuscripts.edit_section_body.execute(manuscript_id, section_id, "Unsaved notes")
    with pytest.raises(UnsavedChangesError):
        history_services.merge_draft.execute(manuscript_id, "review")
    assert history_services.list.execute(manuscript_id) == [initial]
    working = manuscripts.get.execute(manuscript_id)
    assert working is not None
    assert working.sections[0].body == "Unsaved notes"

    manuscripts.edit_section_body.execute(
        manuscript_id, section_id, initial.snapshot.sections[0].body
    )
    merged = history_services.merge_draft.execute(manuscript_id, "review")

    assert history_services.list.execute(manuscript_id) == [merged.head, initial]
    assert merged.head.merged_from == MergeSource("review", source.id)
    assert merged.head.snapshot.sections[0].body == "Reviewed findings"
    working = manuscripts.get.execute(manuscript_id)
    assert working is not None
    assert working.sections[0].body == "Reviewed findings"


def test_failed_merge_save_restores_working_content_and_allows_retry(
    history_services: RevisionHistoryModule,
    history_repository: InMemoryRevisionHistoryRepository,
    manuscript_repository: InMemoryManuscriptRepository,
    publisher: InProcessEventBus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manuscripts = build_manuscript_module(manuscript_repository, publisher)
    manuscript = manuscripts.create.execute(str(ProjectId.new().value), "Thesis", template=False)
    manuscript_id = str(manuscript.id.value)
    manuscripts.append_section.execute(manuscript_id, None, "Results")
    working = manuscripts.get.execute(manuscript_id)
    assert working is not None
    section_id = str(working.sections[0].id.value)
    history_services.start.execute(manuscript_id)
    initial = history_services.list.execute(manuscript_id)
    history_services.create_draft.execute(manuscript_id, "review")
    history_services.switch_draft.execute(manuscript_id, "review")
    manuscripts.edit_section_body.execute(manuscript_id, section_id, "Reviewed findings")
    source = history_services.commit.execute(manuscript_id, None, "Review findings")
    history_services.switch_draft.execute(manuscript_id, "main")

    def reject_save(history: RevisionHistory) -> None:
        pending = manuscripts.get.execute(manuscript_id)
        assert pending is not None
        assert pending.sections[0].body == "Reviewed findings"
        assert history.current_draft.head.merged_from == MergeSource("review", source.id)
        raise ConcurrentModificationError("History changed during the operation.")

    with monkeypatch.context() as patch:
        patch.setattr(history_repository, "save", reject_save)
        with pytest.raises(ConcurrentModificationError):
            history_services.merge_draft.execute(manuscript_id, "review")

    assert history_services.list.execute(manuscript_id) == initial
    assert history_services.list.execute(manuscript_id, "review")[0] == source
    restored = manuscripts.get.execute(manuscript_id)
    assert restored is not None
    assert restored.sections[0].body == ""

    merged = history_services.merge_draft.execute(manuscript_id, "review")
    assert merged.head.merged_from == MergeSource("review", source.id)
