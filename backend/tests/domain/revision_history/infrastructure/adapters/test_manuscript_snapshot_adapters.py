from dataclasses import replace

from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.aggregates import Manuscript
from domain.manuscript.models.events import ManuscriptContentReplaced
from domain.manuscript.models.value_objects import Heading, ManuscriptTitle, ProjectId
from domain.revision_history.infrastructure.adapters.manuscript_repository_reader import (
    ManuscriptRepositoryReader,
)
from domain.revision_history.infrastructure.adapters.manuscript_repository_writer import (
    ManuscriptRepositoryWriter,
)
from domain.revision_history.models.value_objects import Snapshot
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus


def test_snapshot_round_trip_preserves_nested_sections_and_publishes_replacement(
    manuscript_repository: InMemoryManuscriptRepository, publisher: InProcessEventBus
) -> None:
    manuscript = Manuscript.create(ProjectId.new(), ManuscriptTitle("Thesis"), template=False)
    manuscript.append_section(None, Heading("Methods"))
    parent = manuscript.sections[0]
    manuscript.append_section(parent.id, Heading("Sampling"))
    manuscript_repository.save(manuscript)
    manuscript_id = str(manuscript.id.value)
    reader = ManuscriptRepositoryReader(manuscript_repository)
    writer = ManuscriptRepositoryWriter(manuscript_repository, publisher)
    events: list[ManuscriptContentReplaced] = []
    publisher.subscribe(ManuscriptContentReplaced, events.append)

    initial = reader.get_snapshot(manuscript_id)
    assert initial is not None
    root, child = initial.sections
    assert root.id == parent.id.value
    assert child.parent_id == root.id
    updated = Snapshot((root, replace(child, body="Sampling details")))
    writer.apply_snapshot(manuscript_id, updated)

    assert reader.get_snapshot(manuscript_id) == updated
    assert initial.sections[1].body == ""
    assert events == [ManuscriptContentReplaced(manuscript.id.value, manuscript.project_id.value)]
