"""Offline tests for Mongo source mapping and index setup (no server needed)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from domain.src_lib.infrastructure.adapters.mongodb_source_indexes import (
    TEXT_INDEX_NAME,
    TEXT_WEIGHTS,
    ensure_text_index,
)
from domain.src_lib.infrastructure.adapters.mongodb_source_repository import (
    _LIST_PROJECTION,
    MongoSourceRepository,
)
from domain.src_lib.models.value_objects import ContentType


def legacy_doc() -> dict:
    """Shape written before text sources existed (N4)."""
    return {
        "_id": str(uuid4()),
        "title": "Old paper",
        "authors": ["Ada"],
        "year": 1999,
        "file_ref": "/old.pdf",
        "project_id": str(uuid4()),
        "removed_at": None,
        "created_at": datetime(2020, 1, 1, tzinfo=UTC),
    }


def test_legacy_doc_loads_as_file_with_defaults():
    source = MongoSourceRepository._to_source(legacy_doc())
    assert source.kind == "file"
    assert source.content is None and source.description is None
    assert source.tags.value == ()
    assert source.content_type == ContentType.OTHER
    assert source.version == 1
    assert source.updated_at == datetime(2020, 1, 1, tzinfo=UTC)


def test_list_projection_replaces_content_with_snippet():
    assert _LIST_PROJECTION["content"] == {"$substrCP": ["$content", 0, 200]}


def test_save_unsets_cleared_optional_fields():
    coll = MagicMock()
    repo = MongoSourceRepository.__new__(MongoSourceRepository)
    repo._sources = coll
    source = MongoSourceRepository._to_source(legacy_doc())
    repo.save(source)
    update = coll.update_one.call_args.args[1]
    assert update["$unset"] == {"description": "", "content": ""}


def _collection(indexes: list[dict]) -> MagicMock:
    coll = MagicMock()
    coll.list_indexes.return_value = indexes
    return coll


def test_text_index_created_when_absent():
    coll = _collection([{"name": "_id_", "key": {"_id": 1}}])
    ensure_text_index(coll)
    kwargs = coll.create_index.call_args.kwargs
    assert kwargs["weights"] == TEXT_WEIGHTS and kwargs["name"] == TEXT_INDEX_NAME
    coll.drop_index.assert_not_called()


def test_existing_matching_text_index_is_left_alone():
    coll = _collection(
        [{"name": "x", "key": {"_fts": "text", "_ftsx": 1}, "weights": dict(TEXT_WEIGHTS)}]
    )
    ensure_text_index(coll)
    coll.create_index.assert_not_called()
    coll.drop_index.assert_not_called()


def test_existing_text_index_is_extended_preserving_other_fields():
    existing = {
        "name": "old_text",
        "key": {"_fts": "text", "_ftsx": 1},
        "weights": {"title": 1, "notes": 2},
        "default_language": "german",
    }
    coll = _collection([existing])
    ensure_text_index(coll)
    coll.drop_index.assert_called_once_with("old_text")
    kwargs = coll.create_index.call_args.kwargs
    assert kwargs["weights"] == {**TEXT_WEIGHTS, "notes": 2}
    assert kwargs["default_language"] == "german"
