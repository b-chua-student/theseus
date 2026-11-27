import hashlib
from pathlib import Path

from tokenizers import Tokenizer

from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.models.value_objects import Chunk, ChunkId


class TokenWindowChunker(DocumentChunker):
    """Split original text into bounded, overlapping MiniLM token windows."""

    budget = 192
    overlap = 32

    def __init__(self, model_path: Path) -> None:
        """Load the local vocabulary without padding, truncation, or network access."""
        self._tokenizer = Tokenizer.from_file(str(Path(model_path) / "tokenizer.json"))
        self._tokenizer.no_padding()
        self._tokenizer.no_truncation()

    def chunk(self, structured_text: str) -> list[Chunk]:
        """Emit source slices with stable positions and hashes in document order."""
        encoding = self._tokenizer.encode(structured_text, add_special_tokens=False)
        offsets = encoding.offsets
        words = encoding.word_ids
        chunks: list[Chunk] = []
        start = 0
        while start < len(offsets):
            end = min(start + self.budget, len(offsets))
            if end < len(offsets):
                # Prefer whole words at both ends of the shared passage. This avoids
                # changing a WordPiece continuation when a chunk is embedded alone.
                for boundary in range(end, start + self.overlap, -1):
                    following = boundary - self.overlap
                    if (
                        words[boundary - 1] != words[boundary]
                        and words[following - 1] != words[following]
                    ):
                        end = boundary
                        break
            left = offsets[start][0]
            while True:
                right = offsets[end - 1][1]
                passage = structured_text[left:right]
                size = len(self._tokenizer.encode(passage, add_special_tokens=False).ids)
                if size <= self.budget:
                    break
                end -= max(1, size - self.budget)
            chunks.append(
                Chunk(
                    id=ChunkId.new(),
                    text=passage,
                    position=str(len(chunks)),
                    location=f"characters_{left}_{right}",
                    content_hash=hashlib.sha256(passage.encode()).hexdigest(),
                )
            )
            if end == len(offsets):
                break
            start = end - self.overlap
        return chunks
