from abc import ABC, abstractmethod


class VectorStore(ABC):
    @abstractmethod
    def search(
        embedding: Embedding
    )
