from abc import ABC, abstractmethod
from typing import Literal
from uuid import UUID

from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import ContentType, SourceId


class SourceRepository(ABC):
    """Port for persisting and retrieving sources."""

    @abstractmethod
    def get(self, source_id: SourceId) -> Source | None:
        """Return the source with this ID, or None if it does not exist."""
        ...

    @abstractmethod
    def list_active(self) -> list[Source]:
        """Return all sources that have not been removed."""
        ...

    @abstractmethod
    def save(self, source: Source) -> None:
        """Insert or update a source."""
        ...

    @abstractmethod
    def list_text(
        self,
        project_id: UUID,
        content_type: ContentType | None = None,
        tag: str | None = None,
        sort: Literal["updatedAt", "title"] = "updatedAt",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Source], int]:
        """List text sources with filtering, sorting and pagination.

        Returns:
            Tuple of (sources on current page, total count matching filters)
        """
        ...

    @abstractmethod
    def search_text(
        self,
        project_id: UUID,
        query: str,
        content_type: ContentType | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Source], int]:
        """Search text sources with full-text search.

        Returns:
            Tuple of (sources on current page, total count matching search)
        """
        ...
