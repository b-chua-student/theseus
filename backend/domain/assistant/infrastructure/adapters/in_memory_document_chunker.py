"""In-memory document chunker.

Splits text into chunks at double-newline (paragraph) boundaries. Each
non-empty paragraph becomes a single Chunk with a SHA-256 content hash. This
is a simple default; production deployments should swap in a real chunker
(e.g. chonkie) via the container.
"""

import hashlib

from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.models.value_objects import Chunk, ChunkId


class InMemoryDocumentChunker(DocumentChunker):
    """Chunks text by paragraph boundaries."""

    def chunk(self, structured_text: str) -> list[Chunk]:
        paragraphs = [p.strip() for p in structured_text.split("\n\n") if p.strip()]

        chunks: list[Chunk] = []
        for index, paragraph in enumerate(paragraphs):
            chunks.append(
                Chunk(
                    id=ChunkId.new(),
                    text=paragraph,
                    position=str(index),
                    location=f"paragraph_{index}",
                    content_hash=hashlib.sha256(paragraph.encode()).hexdigest(),
                )
            )

        return chunks
