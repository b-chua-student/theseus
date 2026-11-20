from uuid import UUID

from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.value_objects import ContentType
from domain.src_lib.services.list_text_sources import (
    DEFAULT_PAGE_SIZE,
    TextSourcePage,
    normalize_paging,
    parse_content_type,
)


class SearchTextSourcesService:
    """Use case: full-text search over a project's text sources."""

    def __init__(self, repository: SourceRepository) -> None:
        """Initialize the instance."""
        self._repository = repository

    def execute(
        self,
        project_id: UUID,
        query: str,
        content_type: str | ContentType | None = None,
        tag: str | None = None,
        page: int | None = 1,
        page_size: int | None = DEFAULT_PAGE_SIZE,
    ) -> TextSourcePage:
        """Return a page of matching active text sources (empty result is valid).

        Raises:
            ValueError: if `content_type` is invalid.
        """
        page, page_size = normalize_paging(page, page_size)
        items, total = self._repository.search_text(
            project_id,
            (query or "").strip(),
            parse_content_type(content_type),
            tag,
            page,
            page_size,
        )
        return TextSourcePage(items, total, page, page_size)
