from abc import ABC, abstractmethod

from domain.indexing.value_objects import EmbeddingModelRef


class Embedder(ABC):
    """Port for turning text into embedding vectors."""

    @property
    @abstractmethod
    def model(self) -> EmbeddingModelRef:
        """The model that produces the vectors."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in order, returning one vector per text."""
