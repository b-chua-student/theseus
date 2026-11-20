"""Unit tests for the MongoDB source repository."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from domain.src_lib.infrastructure.adapters.mongodb_source_repository import (
    MongoSourceRepository,
)
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)


def make_repository() -> tuple[MongoSourceRepository, MagicMock]:
    """Create a repository with a mocked MongoDB collection."""
    database = MagicMock()
    collection = database.__getitem__.return_value

    with patch(
        "domain.src_lib.infrastructure.adapters.mongodb_source_repository.ensure_source_indexes"
    ):
        repository = MongoSourceRepository(database)

    return repository, collection


def make_source() -> Source:
    """Create a sample text source."""
    return Source.add_text(
        title=SourceTitle("Research"),
        content=TextBody("Sample research content"),
        project_id=uuid4(),
        description=Description.create("Notes"),
        tags=Tags.create(["science"]),
    )


def test_save_source() -> None:
    """Save a source using an upsert."""
    repository, collection = make_repository()
    source = make_source()

    repository.save(source)

    args = collection.update_one.call_args.args
    assert args[0] == {"_id": str(source.id.value)}
    assert args[1]["$set"]["title"] == "Research"
    assert args[1]["$set"]["content"] == "Sample research content"
    assert collection.update_one.call_args.kwargs["upsert"] is True


def test_get_existing_source() -> None:
    """Retrieve and reconstruct a stored source."""
    repository, collection = make_repository()
    source = make_source()
    collection.find_one.return_value = {
        "_id": str(source.id.value),
        "title": "Research",
        "project_id": str(source.project_id),
        "kind": "text",
        "content": "Sample research content",
        "description": "Notes",
        "tags": ["science"],
    }

    result = repository.get(source.id)

    assert result is not None
    assert result.id == source.id
    assert result.title == source.title
    assert result.content == source.content
    assert result.tags == source.tags


def test_get_missing_source() -> None:
    """Return None when a source does not exist."""
    repository, collection = make_repository()
    collection.find_one.return_value = None

    assert repository.get(SourceId.new()) is None


def test_save_removed_source() -> None:
    """Persist the soft-deletion timestamp."""
    repository, collection = make_repository()
    source = make_source()
    source.remove()

    repository.save(source)

    update = collection.update_one.call_args.args[1]
    assert update["$set"]["removed_at"] is not None


def test_save_cleared_description() -> None:
    """Remove an optional description when cleared."""
    repository, collection = make_repository()
    source = make_source()
    source.update_text(
        SourceTitle("Updated"),
        TextBody("Updated content"),
    )

    repository.save(source)

    update = collection.update_one.call_args.args[1]
    assert "description" in update["$unset"]


def test_list_active_filters_removed_sources() -> None:
    """Query only active sources."""
    repository, collection = make_repository()
    collection.find.return_value.sort.return_value = []

    assert repository.list_active() == []

    collection.find.assert_called_once_with({"removed_at": None})


def test_list_text_filters_and_paginates() -> None:
    """Apply project, tag, and pagination constraints."""
    repository, collection = make_repository()
    project_id = uuid4()
    collection.count_documents.return_value = 3

    cursor = collection.find.return_value
    cursor.sort.return_value.collation.return_value.skip.return_value.limit.return_value = []

    results, total = repository.list_text(
        project_id,
        tag="science",
        page=2,
        page_size=1,
    )

    assert results == []
    assert total == 3

    query = {
        "project_id": str(project_id),
        "kind": "text",
        "removed_at": None,
        "tags": "science",
    }

    collection.count_documents.assert_called_once_with(query)
    assert collection.find.call_args.args[0] == query
    cursor.sort.return_value.collation.return_value.skip.assert_called_once_with(1)


def test_search_text_builds_query() -> None:
    """Combine full-text search with project filtering."""
    repository, collection = make_repository()
    project_id = uuid4()
    collection.count_documents.return_value = 0

    cursor = collection.find.return_value
    cursor.sort.return_value.skip.return_value.limit.return_value = []

    results, total = repository.search_text(project_id, " research ")

    expected = {
        "$and": [
            {"$text": {"$search": "research"}},
            {
                "project_id": str(project_id),
                "kind": "text",
                "removed_at": None,
            },
        ]
    }

    assert results == []
    assert total == 0
    collection.count_documents.assert_called_once_with(expected)
    assert collection.find.call_args.args[0] == expected


def test_blank_search_omits_text_query() -> None:
    """Use normal filtering for an empty search."""
    repository, collection = make_repository()
    project_id = uuid4()
    collection.count_documents.return_value = 0

    cursor = collection.find.return_value
    cursor.sort.return_value.skip.return_value.limit.return_value = []

    repository.search_text(project_id, "   ")

    collection.count_documents.assert_called_once_with(
        {
            "project_id": str(project_id),
            "kind": "text",
            "removed_at": None,
        }
    )
