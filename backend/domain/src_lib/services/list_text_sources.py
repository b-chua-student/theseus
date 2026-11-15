from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import ContentType

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
SNIPPET_LENGTH = 200


@dataclass(frozen=True)
class TextSourcePage:
    """One page of text sources plus the total number of matches."""

    items: list[Source]
    total: int
    page: int
    page_size: int


def snippet_of(source: Source) -> str:
    """Return the first 200 characters of a text source's content."""
    return source.content.value[:SNIPPET_LENGTH] if source.content else ""


def normalize_paging(page: int | None, page_size: int | None) -> tuple[int, int]:
    """Clamp page to >= 1 and page_size to 1..100 (default 20)."""
    return max(page or 1, 1), min(max(page_size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)


def parse_content_type(value: str | ContentType | None) -> ContentType | None:
    """Parse an optional content-type filter; invalid values raise ValueError."""
    if value is None or isinstance(value, ContentType):
        return value
    return ContentType(value)


class ListTextSourcesService:
    """Use case: list a project's text sources with filters, sorting and paging."""

    def __init__(self, repository: SourceRepository) -> None:
        self._repository = repository

    def execute(
        self,
        project_id: UUID,
        content_type: str | ContentType | None = None,
        tag: str | None = None,
        sort: Literal["updatedAt", "title"] = "updatedAt",
        page: int | None = 1,
        page_size: int | None = DEFAULT_PAGE_SIZE,
    ) -> TextSourcePage:
        """Return a page of active text sources.

        Raises:
            ValueError: if `content_type` or `sort` is invalid.
        """
        if sort not in ("updatedAt", "title"):
            raise ValueError(f"Invalid sort: {sort}")
        page, page_size = normalize_paging(page, page_size)
        items, total = self._repository.list_text(
            project_id, parse_content_type(content_type), tag, sort, page, page_size
        )
        return TextSourcePage(items, total, page, page_size)
