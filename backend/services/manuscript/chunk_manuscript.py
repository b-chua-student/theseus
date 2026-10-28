from dataclasses import dataclass
from uuid import UUID

from markdownify import markdownify as md  # type: ignore[import-untyped]

from domain.manuscript.aggregates import Manuscript
from ports.chunking.chunker import Chunker, Chunk


@dataclass(frozen=True)
class ChunkedManuscript:
    """A manuscript whose section bodies are chunked, keyed by section id."""

    id: UUID
    project_id: UUID
    title: str
    chunks: dict[UUID, list[Chunk]]


class ChunkManuscriptService:
    """Application service for chunking a manuscript's sections."""

    def __init__(self, chunker: Chunker) -> None:
        self._chunker = chunker

    def execute(self, manuscript: Manuscript) -> ChunkedManuscript:
        chunks: dict[UUID, list[Chunk]] = {}

        for section in manuscript.sections:
            markdown_body: str = md(section.body.value, heading_style="ATX")
            chunks[section.id] = self._chunker.chunk(markdown_body)

        return ChunkedManuscript(
            id=manuscript.id,
            project_id=manuscript.project_id,
            title=manuscript.title,
            chunks=chunks,
        )
