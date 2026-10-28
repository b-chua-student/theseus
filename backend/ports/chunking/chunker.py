from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass(frozen=True)
class Chunk:
    """A chunk of section text."""

    text: str
    start_index: int
    end_index: int
    token_count: int

class Chunker(ABC):
    @abstractmethod
    def __init__(self, chunk_size: int) -> None:
        pass

    @abstractmethod
    def chunk(self, text: str) -> list[Chunk]:
        pass
