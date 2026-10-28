import chonkie

from .chunker import Chunker

from chonkie import RecursiveChunker

from ports.chunking.chunker import Chunk

class ChonkieChunker(Chunker):
    def __init__(self, chunk_size: int) -> None:
        self._chunker = RecursiveChunker.from_recipe(
            "markdown",
            lang="en",
            chunk_size=chunk_size,
        )

    def chunk(self, text: str) -> list[Chunk]:
        chonkie_chunks = self._chunker(text)

        chunks: list[Chunk] = []

        for chonkie_chunk in chonkie_chunks:
            chunks.append(
                Chunk(
                    text=chonkie_chunk.text,
                    start_index=chonkie_chunk.start_index,
                    end_index=chonkie_chunk.end_index,
                    token_count=chonkie_chunk.token_count
                )
            )

        return chunks
            
