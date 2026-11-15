"""In-memory embedding generator.

Produces deterministic 32-dimensional vectors by hashing chunk text. The
vectors are NOT semantically meaningful — this adapter exists so the default
in-memory pipeline can run end to end without an external model. Production
deployments should swap in a real embedding generator via the container.
"""

import hashlib

from domain.assistant.infrastructure.ports.embedding_generator import (
    EmbeddingGenerator,
)
from domain.assistant.models.value_objects import Chunk, Embedding


class InMemoryEmbeddingGenerator(EmbeddingGenerator):
    """Generates hash-based deterministic embeddings (32 dimensions)."""

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        return [
            Embedding(chunk_id=chunk.id, vector=self._hash_to_vector(chunk.text))
            for chunk in chunks
        ]

    @staticmethod
    def _hash_to_vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        return [byte / 127.5 - 1.0 for byte in digest]
