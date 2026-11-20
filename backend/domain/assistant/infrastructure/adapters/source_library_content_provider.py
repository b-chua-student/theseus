"""SourceContentProvider that serves text sources from the source library.

Text sources keep their content in the Source aggregate (no file to fetch). Any
id that is not a text source is delegated to the fallback provider (manuscripts),
so the existing path is unchanged.
"""

from domain.assistant.infrastructure.ports.source_content_provider import (
    SourceContentProvider,
)
from domain.assistant.models.value_objects import DocumentRefId
from domain.src_lib.infrastructure.ports.source_repository import SourceRepository
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceId


class SourceLibraryContentProvider(SourceContentProvider):
    """Returns ``content`` for text sources; delegates everything else to ``fallback``."""

    def __init__(self, repository: SourceRepository, fallback: SourceContentProvider) -> None:
        """Set the source repository and fallback content provider."""
        self._repository = repository
        self._fallback = fallback

    def _text_source(self, doc_ref_id: DocumentRefId) -> Source | None:
        source = self._repository.get(SourceId(doc_ref_id.value))
        if source is not None and source.kind == "text":
            return source
        return None

    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        """Return text source content or fall back. Raise if the source is unavailable."""
        source = self._text_source(doc_ref_id)
        if source is None:
            return self._fallback.get_content(doc_ref_id)
        if source.is_removed or source.content is None:
            # Raising makes the worker mark the document FAILED, so a source removed
            # mid-index never becomes searchable.
            raise ValueError(f"Text source unavailable for doc_ref_id={doc_ref_id}")
        return source.content.value

    def get_title(self, doc_ref_id: DocumentRefId) -> str | None:
        """Return the text source title or delegate to the fallback provider."""
        source = self._text_source(doc_ref_id)
        if source is None:
            return self._fallback.get_title(doc_ref_id)
        return source.title.value
