"""Adapts the manuscript repository into a SourceContentProvider for ingestion.

When the IngestionWorker needs the raw text of a manuscript, this provider
fetches the manuscript by its UUID and concatenates all section headings and
bodies into a single string.
"""

from domain.assistant.infrastructure.ports.source_content_provider import (
    SourceContentProvider,
)
from domain.assistant.models.value_objects import DocumentRefId
from domain.manuscript.infrastructure.ports.manuscript_repository import (
    ManuscriptRepository,
)
from domain.manuscript.models.value_objects import ManuscriptId


class ManuscriptContentProvider(SourceContentProvider):
    """Retrieves the full text content of a manuscript by its reference ID."""

    def __init__(self, repository: ManuscriptRepository) -> None:
        self._repository = repository

    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        manuscript = self._repository.get_by_id(ManuscriptId(doc_ref_id.value))

        if manuscript is None:
            raise ValueError(f"Manuscript not found for doc_ref_id={doc_ref_id}")

        parts: list[str] = []
        for section in manuscript.sections:
            parts.append(f"# {section.heading.value}\n\n{section.body}")

        return "\n\n".join(parts)
