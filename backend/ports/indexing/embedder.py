from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Embedding:
    vector: tuple[float, ...]
    model: EmbeddingModelRef

    @property
    def dimensions(self) -> int:
        return len(self.vector)


class Embedder(ABC):
    @abstractmethod
    def embed(self, text: str, model: EmbeddingModelRef) -> Embedding:
        pass

    @abstractmethod
    def embed_many(self, texts: list[str], model: EmbeddingModelRef) -> list[Embedding]:
        pass
