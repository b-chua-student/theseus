from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.models.value_objects import Chunk, Embedding


class OnnxEmbeddingGenerator(EmbeddingGenerator):
    """Generate normalized MiniLM sentence vectors from a local ONNX snapshot."""

    def __init__(self, model_path: Path) -> None:
        """Open the snapshot's tokenizer and encoder directly from disk."""
        root = Path(model_path)
        self._tokenizer = Tokenizer.from_file(str(root / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=256)
        self._tokenizer.enable_padding()
        self._session = ort.InferenceSession(
            str(root / "onnx" / "model.onnx"), providers=["CPUExecutionProvider"]
        )

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        """Mean-pool unpadded token states in bounded batches and preserve input order."""
        result: list[Embedding] = []
        for start in range(0, len(chunks), 32):
            batch = chunks[start : start + 32]
            encodings = self._tokenizer.encode_batch([chunk.text for chunk in batch])
            mask = np.asarray([item.attention_mask for item in encodings], dtype=np.int64)
            inputs = {
                "input_ids": np.asarray([item.ids for item in encodings], dtype=np.int64),
                "attention_mask": mask,
                "token_type_ids": np.asarray([item.type_ids for item in encodings], dtype=np.int64),
            }
            states = self._session.run(["last_hidden_state"], inputs)[0]
            weights = mask[:, :, None].astype(np.float32)
            pooled = (states * weights).sum(axis=1) / weights.sum(axis=1)
            vectors = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            result.extend(
                Embedding(chunk_id=chunk.id, vector=vector.tolist())
                for chunk, vector in zip(batch, vectors, strict=True)
            )
        return result
