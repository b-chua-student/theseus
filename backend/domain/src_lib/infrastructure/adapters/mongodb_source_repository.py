from typing import Any, Literal
from uuid import UUID

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from domain.shared.clock import now
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


class MongoSourceRepository(SourceRepository):
    """Sources stored one per document. Removed sources are kept (soft delete)."""

    def __init__(self, database: Database, *, collection: str = "sources") -> None:
        self._sources = database[collection]
        self._sources.create_index("removed_at")
        # Create indexes for text search and filtering
        self._sources.create_index(
            [("project_id", 1), ("kind", 1), ("removed_at", 1), ("updated_at", DESCENDING)]
        )
        self._sources.create_index([("project_id", 1), ("tags", 1)])
        # Text index for search - extend existing if present
        try:
            # Check if text index exists
            existing_indexes = list(self._sources.list_indexes())
            has_text_index = any("text" in idx.get("key", {}) for idx in existing_indexes)
            if not has_text_index:
                self._sources.create_index(
                    [
                        ("title", "text"),
                        ("tags", "text"),
                        ("description", "text"),
                        ("content", "text"),
                    ],
                    default_language="english",
                    weights={
                        "title": 10,
                        "tags": 5,
                        "description": 3,
                        "content": 1,
                    },
                )
        except Exception:
            # If text index creation fails (e.g., existing incompatible index), skip
            pass

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
        updated_at = doc.get("updated_at")

        return Source(
            id=SourceId(UUID(doc["_id"])),
            title=SourceTitle(doc["title"]),
            authors=tuple(Author(name) for name in doc["authors"]),
            year=doc["year"],
            file_ref=doc["file_ref"],
            project_id=UUID(doc["project_id"]),
            removed_at=doc["removed_at"],
            kind=kind,
            content=content,
            description=description,
            tags=tags,
            content_type=content_type,
            version=version,
            updated_at=updated_at,
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
        update_fields = {k: v for k, v in doc.items() if k != "_id"}

        self._sources.update_one(
            {"_id": str(source.id.value)},
            {
                "$set": update_fields,
                "$setOnInsert": {"created_at": now()},
            },
            upsert=True,
        )

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
            self._sources.find(query, {"content": 0}).sort(sort_field).skip(skip).limit(page_size)
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
        projection: dict[str, Any] = {"content": 0}
        if text_query:
            projection["score"] = {"$meta": "textScore"}

        # Apply pagination and sort by text score if searching
        skip = (page - 1) * page_size
        cursor = self._sources.find(mongo_query, projection)
        if text_query:
            cursor = cursor.sort([("score", {"$meta": "textScore"}), ("updated_at", DESCENDING)])
        else:
            cursor = cursor.sort("updated_at", DESCENDING)
        docs = cursor.skip(skip).limit(page_size)

        return [self._to_source(d) for d in docs], total
