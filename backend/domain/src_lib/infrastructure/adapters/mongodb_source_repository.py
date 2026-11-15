from typing import Any, Literal
from uuid import UUID

from pymongo import ASCENDING, DESCENDING
from pymongo.collation import Collation
from pymongo.database import Database

from domain.src_lib.infrastructure.adapters.mongodb_source_indexes import ensure_source_indexes
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import (
    Author,
    ContentType,
    Description,
    SourceId,
    SourceTitle,
    Tags,
    TextBody,
)

SNIPPET_LENGTH = 200

# List/search views never load the full body (R4). ``content`` is replaced by its first
# SNIPPET_LENGTH characters so the Source invariant (text => content) still holds.
# Items returned by list_text/search_text are therefore read-only summaries and must
# not be saved back; use ``get`` for the full document.
# A computed field makes this an inclusion projection: retain the metadata explicitly.
_LIST_PROJECTION: dict[str, Any] = {
    "title": 1,
    "authors": 1,
    "year": 1,
    "file_ref": 1,
    "project_id": 1,
    "removed_at": 1,
    "kind": 1,
    "content_type": 1,
    "version": 1,
    "updated_at": 1,
    "created_at": 1,
    "tags": 1,
    "description": 1,
    "content": {"$substrCP": ["$content", 0, SNIPPET_LENGTH]},
}

# Case-insensitive ordering for the title sort.
_TITLE_COLLATION = Collation(locale="en", strength=2)


class MongoSourceRepository(SourceRepository):
    """Sources stored one per document. Removed sources are kept (soft delete)."""

    def __init__(self, database: Database, *, collection: str = "sources") -> None:
        self._sources = database[collection]
        ensure_source_indexes(self._sources)

    # ---- mapping ----
    @staticmethod
    def _to_doc(source: Source) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "_id": str(source.id.value),
            "title": source.title.value,
            "authors": [a.name for a in source.authors],
            "year": source.year,
            "file_ref": source.file_ref,
            "project_id": str(source.project_id),
            "removed_at": source.removed_at,
            "kind": source.kind,
            "content_type": source.content_type.value,
            "version": source.version,
            "updated_at": source.updated_at,
            "created_at": source.created_at,
            "tags": list(source.tags.value),
        }

        # Add text-specific fields if present
        if source.description:
            doc["description"] = source.description.value
        if source.content:
            doc["content"] = source.content.value

        return doc

    @staticmethod
    def _to_source(doc: dict[str, Any]) -> Source:
        # Handle old documents that don't have new fields
        kind = doc.get("kind", "file")
        content_type_str = doc.get("content_type", "other")
        content_type = ContentType.from_str(content_type_str)

        # Get description if present, else None
        description_value = doc.get("description")
        description = Description.create(description_value) if description_value else None

        # Get content if present (for text sources)
        content_value = doc.get("content")
        content = TextBody(content_value) if content_value else None

        # Get tags if present, else empty
        tags_list = doc.get("tags", [])
        tags = Tags.create(tags_list)

        # Get version if present, default to 1
        version = doc.get("version", 1)

        # Get updated_at if present
        updated_at = doc.get("updated_at") or doc.get("created_at")

        return Source(
            id=SourceId(UUID(doc["_id"])),
            title=SourceTitle(doc["title"]),
            authors=tuple(Author(name) for name in doc.get("authors", [])),
            year=doc.get("year"),
            file_ref=doc.get("file_ref"),
            project_id=UUID(doc["project_id"]),
            removed_at=doc.get("removed_at"),
            kind=kind,
            content=content,
            description=description,
            tags=tags,
            content_type=content_type,
            version=version,
            updated_at=updated_at,
            created_at=doc.get("created_at") or updated_at,
        )

    # ---- port implementation ----
    def get(self, source_id: SourceId) -> Source | None:
        doc = self._sources.find_one({"_id": str(source_id.value)})
        return self._to_source(doc) if doc else None

    def list_active(self) -> list[Source]:
        docs = self._sources.find({"removed_at": None}).sort("created_at", 1)
        return [self._to_source(d) for d in docs]

    def save(self, source: Source) -> None:
        doc = self._to_doc(source)
        update_fields = {k: v for k, v in doc.items() if k not in ("_id", "created_at")}
        # Optional text fields cleared by an update must be removed from the stored doc.
        unset_fields = {k: "" for k in ("description", "content") if k not in update_fields}

        update: dict[str, Any] = {
            "$set": update_fields,
            "$setOnInsert": {"created_at": source.created_at},
        }
        if unset_fields:
            update["$unset"] = unset_fields
        self._sources.update_one({"_id": str(source.id.value)}, update, upsert=True)

    def list_text(
        self,
        project_id: UUID,
        content_type: ContentType | None = None,
        tag: str | None = None,
        sort: Literal["updatedAt", "title"] = "updatedAt",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Source], int]:
        """List text sources with filtering, sorting and pagination."""
        # Build query
        query: dict[str, Any] = {
            "project_id": str(project_id),
            "kind": "text",
            "removed_at": None,
        }

        if content_type:
            query["content_type"] = content_type.value

        if tag:
            query["tags"] = tag

        # Count total matching documents
        total = self._sources.count_documents(query)

        # Determine sort order
        sort_field = [("updated_at", DESCENDING)] if sort == "updatedAt" else [("title", ASCENDING)]

        # Apply pagination
        skip = (page - 1) * page_size

        # Projection to exclude content for list views
        docs = (
            self._sources.find(query, _LIST_PROJECTION)
            .sort(sort_field + [("_id", ASCENDING)])
            .collation(_TITLE_COLLATION)
            .skip(skip)
            .limit(page_size)
        )

        return [self._to_source(d) for d in docs], total

    def search_text(
        self,
        project_id: UUID,
        query: str,
        content_type: ContentType | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Source], int]:
        """Search text sources with full-text search."""
        # Build text search query
        query = query.strip()
        text_query: dict[str, Any] = {"$text": {"$search": query}} if query else {}

        # Build filter query
        filter_query: dict[str, Any] = {
            "project_id": str(project_id),
            "kind": "text",
            "removed_at": None,
        }

        if content_type:
            filter_query["content_type"] = content_type.value

        if tag:
            filter_query["tags"] = tag

        # Combine queries
        mongo_query: dict[str, Any] = (
            {"$and": [text_query, filter_query]} if text_query else filter_query
        )

        # Count total matching documents
        total = self._sources.count_documents(mongo_query)

        # Projection to exclude content for search results
        projection: dict[str, Any] = dict(_LIST_PROJECTION)
        if text_query:
            projection["score"] = {"$meta": "textScore"}

        # Apply pagination and sort by text score if searching
        skip = (page - 1) * page_size
        cursor = self._sources.find(mongo_query, projection)
        if text_query:
            cursor = cursor.sort([("score", {"$meta": "textScore"}), ("updated_at", DESCENDING)])
        else:
            cursor = cursor.sort([("updated_at", DESCENDING), ("_id", ASCENDING)])
        docs = cursor.skip(skip).limit(page_size)

        return [self._to_source(d) for d in docs], total
