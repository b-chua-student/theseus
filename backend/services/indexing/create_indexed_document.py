import hashlib
from uuid import uuid4

from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import (
    ChunkLocation,
    ContentHash,
    EmbeddingModelRef,
    OwnerKind,
)
from services.manuscript.chunk_manuscript import ChunkedManuscript


class CreateIndexedDocumentService:
    """Application service for creating an indexed document from a chunked manuscript."""

    def __init__(self, model: EmbeddingModelRef) -> None:
        self._model = model 

    def execute(self, chunked_manuscript: ChunkedManuscript) -> IndexedDocument:
        """Build, persist, and return a pending indexed document."""
        content_hash = self._hash(chunked_manuscript)

        indexed_document = IndexedDocument.create(
            owner_kind=OwnerKind.MANUSCRIPT,
            owner_id=chunked_manuscript.id,
            content_hash=content_hash,
            model=self._model,
        )

        ordinal = 0
        for section_id, section_chunks in chunked_manuscript.chunks.items():
            for chunk in section_chunks:
                indexed_document.add_chunk(
                    chunk_id=uuid4(),
                    ordinal=ordinal,
                    text=chunk.text,
                    location=ChunkLocation(
                        section_id=section_id,
                        start_index=chunk.start_index,
                        end_index=chunk.end_index,
                    ),
                )
                ordinal += 1

        return indexed_document

    @staticmethod
    def _hash(chunked_manuscript: ChunkedManuscript) -> ContentHash:
        digest = hashlib.sha256()
        for section_id, section_chunks in chunked_manuscript.chunks.items():
            digest.update(str(section_id).encode())
            for chunk in section_chunks:
                digest.update(chunk.text.encode())
        return ContentHash(digest.hexdigest())
