from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import Embedding
from ports.embedding.embedder import Embedder
from repositories.indexing.indexed_document_repository import (
    IndexedDocumentRepository,
)


class EmbedIndexedDocumentService:
    def __init__(self, embedder: Embedder, batch_size: int = 32) -> None:
        if batch_size < 1:
            raise ValueError("Batch size must be at least 1")
        self._embedder = embedder
        self._batch_size = batch_size

    def execute(self, indexed_document: IndexedDocument) -> list[Embedding]:
        if indexed_document.model != self._embedder.model:
            raise ValueError("Embedder model does not match the document model")

        chunks = indexed_document.chunks
        vectors = self._embed_in_batches([chunk.text for chunk in chunks])

        return [
            Embedding(chunk_id=chunk.id, value=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]

    def _embed_in_batches(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []

        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            batch_vectors = self._embedder.embed(batch)

            if len(batch_vectors) != len(batch):
                raise ValueError("Embedder returned the wrong number of vectors")

            vectors.extend(batch_vectors)

        return vectors
