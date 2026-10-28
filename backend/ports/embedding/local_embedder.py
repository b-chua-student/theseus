from fastembed import TextEmbedding

from domain.indexing.value_objects import EmbeddingModelRef
from ports.embedding.embedder import Embedder


class LocalEmbedder(Embedder):
    """Embedder that runs a small ONNX model locally on CPU via fastembed."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self._encoder = TextEmbedding(model_name=model_name)
        self._model = EmbeddingModelRef(
            name=model_name,
            version=f"dim={self._encoder.embedding_size}",
        )

    @property
    def model(self) -> EmbeddingModelRef:
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        return [[float(x) for x in vector] for vector in self._encoder.embed(texts)]
