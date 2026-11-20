"""Unit tests for Source Library text source services."""

from uuid import uuid4

import pytest

from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import (
    InProcessEventBus,
)
from domain.src_lib.models.events import SourceAdded, SourceRemoved, SourceUpdated
from domain.src_lib.models.value_objects import SourceTitle, TextBody
from domain.src_lib.services.add_text_source import AddTextSourceService
from domain.src_lib.services.errors import SourceNotFound
from domain.src_lib.services.get_source import GetSourceService
from domain.src_lib.services.list_text_sources import ListTextSourcesService
from domain.src_lib.services.remove_source import RemoveSourceService
from domain.src_lib.services.search_text_sources import SearchTextSourcesService
from domain.src_lib.services.update_text_source import UpdateTextSourceService


@pytest.fixture
def repository() -> InMemorySourceRepository:
    """Provide an isolated repository."""
    return InMemorySourceRepository()


@pytest.fixture
def publisher() -> InProcessEventBus:
    """Provide an isolated event publisher."""
    return InProcessEventBus()


def test_add_text_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that a text source is saved."""
    project_id = uuid4()
    source_id = AddTextSourceService(repository, publisher).execute(
        title="Research Notes",
        content="Sample content",
        project_id=project_id,
    )

    source = repository.get(source_id)

    assert source is not None
    assert source.title == SourceTitle("Research Notes")
    assert source.content == TextBody("Sample content")
    assert source.project_id == project_id
    assert source.kind == "text"


def test_add_publishes_event(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that adding a source publishes an event."""
    events: list[SourceAdded] = []
    publisher.subscribe(SourceAdded, events.append)

    AddTextSourceService(repository, publisher).execute(
        title="Notes",
        content="Sample content",
        project_id=uuid4(),
    )

    assert len(events) == 1


def test_get_existing_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that an existing source can be retrieved."""
    source_id = AddTextSourceService(repository, publisher).execute(
        title="Notes",
        content="Sample content",
        project_id=uuid4(),
    )

    source = GetSourceService(repository).execute(str(source_id.value))

    assert source is not None
    assert source.id == source_id


def test_get_missing_source(
    repository: InMemorySourceRepository,
) -> None:
    """Verify that a missing source returns None."""
    assert GetSourceService(repository).execute(str(uuid4())) is None


def test_update_text_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that updates replace text and increment version."""
    project_id = uuid4()
    source_id = AddTextSourceService(repository, publisher).execute(
        title="Original",
        content="Original content",
        project_id=project_id,
    )

    UpdateTextSourceService(repository, publisher).execute(
        source_id=str(source_id.value),
        title="Updated",
        content="Updated content",
        project_id=project_id,
    )

    source = repository.get(source_id)

    assert source is not None
    assert source.title == SourceTitle("Updated")
    assert source.content == TextBody("Updated content")
    assert source.version == 2


def test_update_publishes_event(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that updating publishes a SourceUpdated event."""
    events: list[SourceUpdated] = []
    publisher.subscribe(SourceUpdated, events.append)

    source_id = AddTextSourceService(repository, publisher).execute(
        title="Notes",
        content="Original content",
        project_id=uuid4(),
    )

    UpdateTextSourceService(repository, publisher).execute(
        source_id=str(source_id.value),
        title="Updated",
        content="New content",
    )

    assert len(events) == 1


def test_update_missing_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Reject updates to nonexistent sources."""
    with pytest.raises(SourceNotFound):
        UpdateTextSourceService(repository, publisher).execute(
            source_id=str(uuid4()),
            title="Updated",
            content="New content",
        )


def test_update_rejects_wrong_project(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Prevent updates from another project."""
    source_id = AddTextSourceService(repository, publisher).execute(
        title="Original",
        content="Original content",
        project_id=uuid4(),
    )

    with pytest.raises(SourceNotFound):
        UpdateTextSourceService(repository, publisher).execute(
            source_id=str(source_id.value),
            title="Updated",
            content="New content",
            project_id=uuid4(),
        )

    source = repository.get(source_id)

    assert source is not None
    assert source.title == SourceTitle("Original")
    assert source.version == 1


def test_remove_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that removing a source performs a soft delete."""
    source_id = AddTextSourceService(repository, publisher).execute(
        title="Notes",
        content="Sample content",
        project_id=uuid4(),
    )

    RemoveSourceService(repository, publisher).execute(str(source_id.value))

    source = repository.get(source_id)

    assert source is not None
    assert source.is_removed


def test_remove_publishes_event(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify that removal publishes a SourceRemoved event."""
    events: list[SourceRemoved] = []
    publisher.subscribe(SourceRemoved, events.append)

    source_id = AddTextSourceService(repository, publisher).execute(
        title="Notes",
        content="Sample content",
        project_id=uuid4(),
    )

    RemoveSourceService(repository, publisher).execute(str(source_id.value))

    assert len(events) == 1


def test_remove_missing_source(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Reject removal of a nonexistent source."""
    with pytest.raises(SourceNotFound):
        RemoveSourceService(repository, publisher).execute(str(uuid4()))


def test_list_sources_by_project(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Return only sources belonging to the requested project."""
    project_id = uuid4()
    service = AddTextSourceService(repository, publisher)

    source_id = service.execute("Notes", "Content", project_id)
    service.execute("Other Notes", "Other content", uuid4())

    result = ListTextSourcesService(repository).execute(project_id)

    assert result.total == 1
    assert [source.id for source in result.items] == [source_id]


def test_list_excludes_removed_sources(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Exclude removed sources from listing results."""
    project_id = uuid4()
    source_id = AddTextSourceService(repository, publisher).execute("Notes", "Content", project_id)

    RemoveSourceService(repository, publisher).execute(str(source_id.value))

    result = ListTextSourcesService(repository).execute(project_id)

    assert result.total == 0
    assert result.items == []


def test_list_pagination(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify pagination preserves the total number of matches."""
    project_id = uuid4()
    service = AddTextSourceService(repository, publisher)

    for index in range(3):
        service.execute(f"Notes {index}", "Content", project_id)

    result = ListTextSourcesService(repository).execute(project_id, page=1, page_size=2)

    assert result.total == 3
    assert len(result.items) == 2


def test_list_clamps_pagination(
    repository: InMemorySourceRepository,
) -> None:
    """Normalize out-of-range pagination values."""
    result = ListTextSourcesService(repository).execute(uuid4(), page=-1, page_size=500)

    assert result.page == 1
    assert result.page_size == 100


def test_search_text_content(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Find text sources using case-insensitive content search."""
    project_id = uuid4()
    service = AddTextSourceService(repository, publisher)

    source_id = service.execute("Notes", "Artificial Intelligence", project_id)
    service.execute("Other Notes", "Computer networks", project_id)

    result = SearchTextSourcesService(repository).execute(project_id, "  intelligence  ")

    assert result.total == 1
    assert [source.id for source in result.items] == [source_id]


def test_search_no_matches(
    repository: InMemorySourceRepository,
) -> None:
    """Return an empty result when no sources match."""
    result = SearchTextSourcesService(repository).execute(uuid4(), "unknown")

    assert result.total == 0
    assert result.items == []


def test_list_filters_by_tag(
    repository: InMemorySourceRepository,
    publisher: InProcessEventBus,
) -> None:
    """Verify filtering by a specific source tag."""
    project_id = uuid4()
    service = AddTextSourceService(repository, publisher)

    source_id = service.execute("Research", "Content", project_id, tags=["research"])
    service.execute("Other", "Content", project_id, tags=["personal"])

    result = ListTextSourcesService(repository).execute(project_id, tag="research")

    assert result.total == 1
    assert [source.id for source in result.items] == [source_id]
