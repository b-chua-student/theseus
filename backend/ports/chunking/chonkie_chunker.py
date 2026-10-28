from .chunker import Chunker

from chonkie import RecursiveChunker, Chunk

class ChonkieChunker(Chunker):
    def __init__(self, chunk_size: int) -> None:
        self.chunker = RecursiveChunker(chunk_size=chunk_size).from_recipe("markdown", lang="en")

    def chunk(text: str) -> list[Chunk]
        return self.chunker(text)