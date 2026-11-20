"""Unit tests for the in-memory source repository."""

from uuid import UUID, uuid4

from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


def make_source(project_id: UUID, title: str = "Research") -> Source:
    """Create a text source for repository tests."""
    return Source.add_text(
        title=SourceTitle(title),
        content=TextBody("Sample research content"),
        project_id=project_id,
        description=Description.create("Research notes"),
        tags=Tags.create(["science"]),
    )


def test_save_and_get_source() -> None:
    """Retrieve a previously saved source."""
    repository = InMemorySourceRepository()
    source = make_source(uuid4())

    repository.save(source)

    assert repository.get(source.id) == source


def test_get_unknown_source() -> None:
    """Return None for an unknown identifier."""
    repository = InMemorySourceRepository()

    assert repository.get(SourceId.new()) is None


def test_save_updated_source() -> None:
    """Store updated source information."""
    repository = InMemorySourceRepository()
    source = make_source(uuid4())
    repository.save(source)

    source.update_text(
        SourceTitle("Updated research"),
        TextBody("Updated content"),
    )
    repository.save(source)

    stored = repository.get(source.id)
    assert stored is not None
    assert stored.title.value == "Updated research"
    assert stored.version == 2


def test_list_active_excludes_removed_sources() -> None:
    """Exclude soft-deleted sources from active results."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    active = make_source(project_id)
    removed = make_source(project_id)

    removed.remove()
    repository.save(active)
    repository.save(removed)

    assert repository.list_active() == [active]


def test_list_text_filters_project() -> None:
    """Return only sources belonging to the requested project."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)

    repository.save(source)
    repository.save(make_source(uuid4()))

    results, total = repository.list_text(project_id)

    assert results == [source]
    assert total == 1


def test_list_text_excludes_file_sources() -> None:
    """Exclude uploaded files from text source results."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    file_source = Source.add(
        title=SourceTitle("Document"),
        file_ref="document.pdf",
        project_id=project_id,
    )

    repository.save(source)
    repository.save(file_source)

    results, total = repository.list_text(project_id)

    assert results == [source]
    assert total == 1


def test_list_text_filters_tags() -> None:
    """Return sources matching the requested tag."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    repository.save(source)

    results, total = repository.list_text(project_id, tag="science")

    assert results == [source]
    assert total == 1

    results, total = repository.list_text(project_id, tag="history")

    assert results == []
    assert total == 0


def test_list_text_sorts_by_title() -> None:
    """Sort titles alphabetically regardless of case."""
    repository = InMemorySourceRepository()
    project_id = uuid4()

    for title in ("Zebra", "apple", "Banana"):
        repository.save(make_source(project_id, title))

    results, total = repository.list_text(project_id, sort="title")

    assert [source.title.value for source in results] == [
        "apple",
        "Banana",
        "Zebra",
    ]
    assert total == 3


def test_list_text_pagination() -> None:
    """Return the requested page and total matching count."""
    repository = InMemorySourceRepository()
    project_id = uuid4()

    for title in ("Alpha", "Beta", "Gamma"):
        repository.save(make_source(project_id, title))

    results, total = repository.list_text(
        project_id,
        sort="title",
        page=2,
        page_size=1,
    )

    assert len(results) == 1
    assert results[0].title.value == "Beta"
    assert total == 3


def test_search_text_case_insensitive() -> None:
    """Match search queries regardless of letter case."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    repository.save(source)

    results, total = repository.search_text(project_id, "RESEARCH")

    assert results == [source]
    assert total == 1


def test_search_text_matches_content() -> None:
    """Find sources through their text content."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    repository.save(source)

    results, total = repository.search_text(project_id, "Sample")

    assert results == [source]
    assert total == 1


def test_search_text_no_matches() -> None:
    """Return empty results for an unmatched query."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    repository.save(make_source(project_id))

    results, total = repository.search_text(project_id, "unmatched")

    assert results == []
    assert total == 0


def test_search_text_excludes_removed_sources() -> None:
    """Exclude removed sources from search results."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    source.remove()
    repository.save(source)

    results, total = repository.search_text(project_id, "research")

    assert results == []
    assert total == 0


def test_search_text_blank_query() -> None:
    """Treat a blank search query as a normal listing."""
    repository = InMemorySourceRepository()
    project_id = uuid4()
    source = make_source(project_id)
    repository.save(source)

    assert repository.search_text(project_id, "   ") == repository.list_text(project_id)
