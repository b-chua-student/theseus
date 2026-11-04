from abc import ABC, abstractmethod

from domain.assistant.models.value_objects import Chunk, Embedding


class EmbeddingGenerator(ABC):
    """Generates embeddings for a list of text chunks."""

    @abstractmethod
    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        """Return one embedding per chunk, in the same order as ``chunks``."""
