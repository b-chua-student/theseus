"""Index setup for the Mongo ``sources`` collection."""

import logging
from typing import Any

from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

logger = logging.getLogger(__name__)

TEXT_INDEX_NAME = "sources_text"
TEXT_WEIGHTS: dict[str, int] = {"title": 10, "tags": 5, "description": 3, "content": 1}


def _find_text_index(collection: Collection) -> dict[str, Any] | None:
    """Return the collection's text index spec, if any (Mongo allows only one)."""
    for idx in collection.list_indexes():
        if "_fts" in idx.get("key", {}):
            return dict(idx)
    return None


def ensure_text_index(collection: Collection) -> None:
    """Create the text index, or extend an existing one with the weights we need.

    Mongo permits a single text index per collection. If one already exists, its
    weights are merged with ours (existing fields kept, ours win on conflict) and the
    index is rebuilt only when the merged weights differ.
    """
    existing = _find_text_index(collection)
    weights = dict(TEXT_WEIGHTS)
    name = TEXT_INDEX_NAME
    language = "english"

    if existing is not None:
        current: dict[str, int] = dict(existing.get("weights", {}))
        weights = {**current, **TEXT_WEIGHTS}
        if weights == current:
            return
        name = TEXT_INDEX_NAME
        language = existing.get("default_language", language)
        collection.drop_index(existing["name"])

    collection.create_index(
        [(field, "text") for field in weights],
        name=name,
        default_language=language,
        weights=weights,
    )


def ensure_source_indexes(collection: Collection) -> None:
    """Create all indexes required by source queries. Idempotent."""
    collection.create_index("removed_at")
    collection.create_index(
        [("project_id", 1), ("kind", 1), ("removed_at", 1), ("updated_at", DESCENDING)]
    )
    collection.create_index([("project_id", 1), ("tags", 1)])
    try:
        ensure_text_index(collection)
    except OperationFailure:
        logger.exception("Could not create or extend the sources text index")
        raise
