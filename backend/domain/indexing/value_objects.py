from dataclasses import dataclass
from enum import Enum
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IndexedDocumentId:
    """Identifier of an indexed document."""

    value: UUID


class OwnerKind(Enum):
    """Kind of entity that owns an indexed document."""

    MANUSCRIPT = "manuscript"


class IndexStatus(Enum):
    """Lifecycle state of an index."""

    PENDING = "pending"
    READY = "ready"
    STALE = "stale"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ContentHash:
    """Hash of the indexed content."""

    value: str

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the hash is empty.
        """
        if not self.value.strip():
            raise ValueError("Content hash cannot be empty")


@dataclass(frozen=True, slots=True)
class EmbeddingModelRef:
    """Reference to the embedding model used for the index."""

    name: str
    version: str = ""

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the model name is empty.
        """
        if not self.name.strip():
            raise ValueError("Model name cannot be empty")


@dataclass(frozen=True, slots=True)
class ChunkLocation:
    """Where a chunk sits in its source."""

    section_id: UUID
    start_index: int
    end_index: int

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the range is invalid.
        """
        if self.start_index < 0 or self.end_index < self.start_index:
            raise ValueError("Invalid chunk location range")


@dataclass(frozen=True, slots=True)
class Embedding:
    """Embedding vector for a chunk."""

    chunk_id: UUID
    value: list[float]
