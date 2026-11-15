from datetime import datetime
from typing import Literal
from uuid import UUID

from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import ContentType, SourceId


class InMemorySourceRepository(SourceRepository):
    """Non-persistent source repository backed by a dict, for tests."""

    def __init__(self) -> None:
        self._db: dict[SourceId, Source] = {}

    def get(self, source_id: SourceId) -> Source | None:
        return self._db.get(source_id)

    def list_active(self) -> list[Source]:
        return [s for s in self._db.values() if not s.is_removed]

    def save(self, source: Source) -> None:
        self._db[source.id] = source

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
        # Filter: text sources only, active, matching project, optional filters
        filtered = []
        for source in self._db.values():
            if source.is_removed:
                continue
            if source.kind != "text":
                continue
            if source.project_id != project_id:
                continue
            if content_type and source.content_type != content_type:
                continue
            if tag and tag not in source.tags.value:
                continue
            filtered.append(source)

        # Sort
        if sort == "updatedAt":
            filtered.sort(key=lambda s: s.updated_at or datetime.min, reverse=True)
        elif sort == "title":
            filtered.sort(key=lambda s: s.title.value.lower())

        # Paginate
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return paginated, total

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
        if not query:
            return self.list_text(project_id, content_type, tag, "updatedAt", page, page_size)

        query_lower = query.lower()
        filtered = []

        for source in self._db.values():
            if source.is_removed:
                continue
            if source.kind != "text":
                continue
            if source.project_id != project_id:
                continue
            if content_type and source.content_type != content_type:
                continue
            if tag and tag not in source.tags.value:
                continue

            # Search in title, description, tags, and content
            matches = (
                query_lower in source.title.value.lower()
                or (source.description and query_lower in source.description.value.lower())
                or any(query_lower in tag.lower() for tag in source.tags.value)
                or (source.content and query_lower in source.content.value.lower())
            )

            if matches:
                filtered.append(source)

        # Sort by updated_at desc for search results
        filtered.sort(key=lambda s: s.updated_at or datetime.min, reverse=True)

        # Paginate
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = filtered[start:end]

        return paginated, total
