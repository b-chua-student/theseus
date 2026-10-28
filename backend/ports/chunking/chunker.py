from abc import ABC, abstractmethod

class Chunker(ABC):
    @abstractmethod
    def __init__(self, chunk_size: int) -> None:
        pass

    @abstractmethod
    def chunk(text: str, chunk_size: int) -> list[Chunk]:
        pass
