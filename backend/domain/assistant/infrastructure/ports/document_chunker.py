from abc import ABC, abstractmethod

from domain.assistant.models.value_objects import Chunk


class DocumentChunker(ABC):
    """Port for splitting structured document text into retrievable chunks."""

    @abstractmethod
    def chunk(self, structured_text: str) -> list[Chunk]:
        """Split ``structured_text`` into ordered chunks."""
