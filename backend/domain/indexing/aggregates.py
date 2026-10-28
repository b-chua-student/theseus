from __future__ import annotations

from uuid import UUID, uuid4

from .entities import Chunk
from .value_objects import (
    ChunkLocation,
    ContentHash,
    EmbeddingModelRef,
    IndexedDocumentId,
    IndexStatus,
    OwnerKind,
)


class IndexedDocument:
    """Aggregate root for an indexed document and its chunks."""

    def __init__(
        self,
        indexed_document_id: IndexedDocumentId,
        owner_kind: OwnerKind,
        owner_id: UUID,
        content_hash: ContentHash,
        model: EmbeddingModelRef,
        status: IndexStatus = IndexStatus.PENDING,
    ) -> None:
        self._id = indexed_document_id
        self._owner_kind = owner_kind
        self._owner_id = owner_id
        self._content_hash = content_hash
        self._model = model
        self._status = status
        self._chunks: dict[UUID, Chunk] = {}

    @classmethod
    def create(
        cls,
        owner_kind: OwnerKind,
        owner_id: UUID,
        content_hash: ContentHash,
        model: EmbeddingModelRef,
    ) -> IndexedDocument:
        """Create a pending indexed document with a new id."""
        return cls(
            indexed_document_id=IndexedDocumentId(uuid4()),
            owner_kind=owner_kind,
            owner_id=owner_id,
            content_hash=content_hash,
            model=model,
        )

    @property
    def indexed_document_id(self) -> IndexedDocumentId:
        return self._id

    @property
    def owner_kind(self) -> OwnerKind:
        return self._owner_kind

    @property
    def owner_id(self) -> UUID:
        return self._owner_id

    @property
    def content_hash(self) -> ContentHash:
        return self._content_hash

    @property
    def status(self) -> IndexStatus:
        return self._status

    @property
    def model(self) -> EmbeddingModelRef:
        return self._model

    @property
    def chunks(self) -> list[Chunk]:
        """Chunks ordered by ordinal."""
        return sorted(self._chunks.values(), key=lambda chunk: chunk.ordinal)

    def update_status(self, status: IndexStatus) -> None:
        self._status = status

    def update_content_hash(self, content_hash: ContentHash) -> None:
        self._content_hash = content_hash

    def change_model(self, model: EmbeddingModelRef) -> None:
        """Change the embedding model. Marks the index stale."""
        self._model = model
        self._status = IndexStatus.STALE

    def add_chunk(
        self,
        chunk_id: UUID,
        ordinal: int,
        text: str,
        location: ChunkLocation,
    ) -> Chunk:
        """Add a chunk.

        Raises:
            ValueError: If the id or ordinal is already used.
        """
        if chunk_id in self._chunks:
            raise ValueError("Chunk already exists")
        if any(chunk.ordinal == ordinal for chunk in self._chunks.values()):
            raise ValueError("Chunk ordinal already used")

        chunk = Chunk(
            id=chunk_id,
            indexed_document_id=self._id,
            ordinal=ordinal,
            text=text,
            location=location,
        )
        self._chunks[chunk.id] = chunk
        return chunk

    def get_chunk(self, chunk_id: UUID) -> Chunk:
        """Raises:
        ValueError: If the chunk does not exist.
        """
        try:
            return self._chunks[chunk_id]
        except KeyError:
            raise ValueError("Chunk does not exist") from None

    def remove_chunk(self, chunk_id: UUID) -> None:
        """Raises:
        ValueError: If the chunk does not exist.
        """
        self.get_chunk(chunk_id)
        del self._chunks[chunk_id]
