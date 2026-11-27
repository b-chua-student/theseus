from bootstrap.contexts.manuscript.module import build_manuscript_module
from domain.manuscript.infrastructure.adapters.in_memory_manuscript_repository import (
    InMemoryManuscriptRepository,
)
from domain.manuscript.models.events import ManuscriptSaved
from domain.manuscript.models.value_objects import ProjectId
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus


def test_body_edit_persists_and_publishes_the_saved_section() -> None:
    repository = InMemoryManuscriptRepository(template=False)
    publisher = InProcessEventBus()
    events: list[ManuscriptSaved] = []
    publisher.subscribe(ManuscriptSaved, events.append)
    services = build_manuscript_module(repository, publisher)
    manuscript = services.create.execute(str(ProjectId.new().value), "Thesis", template=False)
    manuscript_id = str(manuscript.id.value)
    services.append_section.execute(manuscript_id, None, "Results")
    stored = services.get.execute(manuscript_id)
    assert stored is not None
    section_id = stored.sections[0].id.value

    services.edit_section_body.execute(manuscript_id, str(section_id), "Observed results")

    updated = services.get.execute(manuscript_id)
    assert updated is not None
    assert updated.sections[0].body == "Observed results"
    assert events == [
        ManuscriptSaved(
            manuscript.id.value, manuscript.project_id.value, section_id, "Observed results"
        )
    ]
