"""Unit tests for MongoDB source indexes."""

from unittest.mock import MagicMock

import pytest
from pymongo.errors import OperationFailure

from domain.src_lib.infrastructure.adapters.mongodb_source_indexes import (
    TEXT_INDEX_NAME,
    TEXT_WEIGHTS,
    ensure_source_indexes,
    ensure_text_index,
)


def test_create_text_index() -> None:
    """Create a text index when none exists."""
    collection = MagicMock()
    collection.list_indexes.return_value = []

    ensure_text_index(collection)

    collection.create_index.assert_called_once_with(
        [(field, "text") for field in TEXT_WEIGHTS],
        name=TEXT_INDEX_NAME,
        default_language="english",
        weights=TEXT_WEIGHTS,
    )
    collection.drop_index.assert_not_called()


def test_keep_existing_text_index() -> None:
    """Avoid rebuilding an index with matching weights."""
    collection = MagicMock()
    collection.list_indexes.return_value = [
        {
            "name": TEXT_INDEX_NAME,
            "key": {"_fts": "text"},
            "weights": dict(TEXT_WEIGHTS),
        }
    ]

    ensure_text_index(collection)

    collection.create_index.assert_not_called()
    collection.drop_index.assert_not_called()


def test_extend_existing_text_index() -> None:
    """Preserve existing fields while adding required weights."""
    collection = MagicMock()
    collection.list_indexes.return_value = [
        {
            "name": "old_index",
            "key": {"_fts": "text"},
            "weights": {"notes": 2, "title": 1},
            "default_language": "english",
        }
    ]

    ensure_text_index(collection)

    expected = {"notes": 2, **TEXT_WEIGHTS}

    collection.drop_index.assert_called_once_with("old_index")
    collection.create_index.assert_called_once_with(
        [(field, "text") for field in expected],
        name=TEXT_INDEX_NAME,
        default_language="english",
        weights=expected,
    )


def test_create_required_source_indexes() -> None:
    """Create indexes required by source queries."""
    collection = MagicMock()
    collection.list_indexes.return_value = []

    ensure_source_indexes(collection)

    collection.create_index.assert_any_call("removed_at")
    collection.create_index.assert_any_call(
        [
            ("project_id", 1),
            ("kind", 1),
            ("removed_at", 1),
            ("updated_at", -1),
        ]
    )
    collection.create_index.assert_any_call([("project_id", 1), ("tags", 1)])
    assert collection.create_index.call_count == 4


def test_index_creation_failure() -> None:
    """Propagate MongoDB text index creation failures."""
    collection = MagicMock()
    collection.list_indexes.return_value = []
    collection.create_index.side_effect = [
        None,
        None,
        None,
        OperationFailure("Index creation failed"),
    ]

    with pytest.raises(OperationFailure, match="Index creation failed"):
        ensure_source_indexes(collection)
