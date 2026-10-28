from dataclasses import dataclass
from uuid import UUID

from .value_objects import ChunkLocation, IndexedDocumentId


@dataclass(eq=False)
class Chunk:
    """A chunk of indexed text."""

    id: UUID
    indexed_document_id: IndexedDocumentId
    ordinal: int
    text: str
    location: ChunkLocation

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the ordinal is negative or the text is empty.
        """
        if self.ordinal < 0:
            raise ValueError("Chunk ordinal cannot be negative")
        if not self.text.strip():
            raise ValueError("Chunk text cannot be empty")
