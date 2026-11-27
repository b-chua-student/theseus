"""Semantic embedding generator backed by the Gemini embedding API.

Indexing and query embeddings must come from the same model, because cosine scores are only
comparable within one embedding space. When the model changes, re-embed existing documents with
``flask reindex-documents`` (see ``ReindexDocumentsService``).
"""

import os
from typing import Protocol

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.models.errors import EmbeddingGenerationError
from domain.assistant.models.value_objects import Chunk, Embedding

DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_TIMEOUT_MS = 30_000
# The Gemini API embeds at most 100 inputs per request.
MAX_BATCH_SIZE = 100


class EmbeddingModels(Protocol):
    """The part of ``genai.Client.models`` this adapter uses."""

    def embed_content(
        self, *, model: str, contents: list[str], config: types.EmbedContentConfig
    ) -> types.EmbedContentResponse:
        """Embed each content string."""
        ...


class EmbeddingClient(Protocol):
    """The part of ``genai.Client`` this adapter uses."""

    @property
    def models(self) -> EmbeddingModels:
        """Return the models API."""
        ...


class GeminiEmbeddingGenerator(EmbeddingGenerator):
    """EmbeddingGenerator that calls the Gemini embedding model in batches."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_EMBEDDING_MODEL,
        output_dimensionality: int | None = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        client: EmbeddingClient | None = None,
    ) -> None:
        """Configure the client and model.

        Raises:
            ValueError: If no client is given and GEMINI_API_KEY is not set.
        """
        if client is None:
            load_dotenv()
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("GEMINI_API_KEY is not set")
            client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=timeout_ms))
        self._client = client
        self._model = model
        self._config = types.EmbedContentConfig(output_dimensionality=output_dimensionality)

    @property
    def model(self) -> str:
        """Return the embedding model name."""
        return self._model

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        """Return one embedding per chunk, in order.

        Raises:
            EmbeddingGenerationError: If the provider fails or returns the wrong vectors.
        """
        embeddings: list[Embedding] = []
        for start in range(0, len(chunks), MAX_BATCH_SIZE):
            batch = chunks[start : start + MAX_BATCH_SIZE]
            embeddings.extend(self._embed(batch))
        return embeddings

    def _embed(self, batch: list[Chunk]) -> list[Embedding]:
        try:
            response = self._client.models.embed_content(
                model=self._model, contents=[chunk.text for chunk in batch], config=self._config
            )
        except genai_errors.APIError as exc:
            raise EmbeddingGenerationError(
                f"The embedding provider returned an error ({exc.code})."
            ) from exc
        except Exception as exc:  # network failures, timeouts, SDK errors
            raise EmbeddingGenerationError("Could not reach the embedding provider.") from exc

        vectors = [embedding.values for embedding in response.embeddings or []]
        if len(vectors) != len(batch):
            raise EmbeddingGenerationError(
                f"Expected {len(batch)} embeddings, received {len(vectors)}."
            )
        result = []
        for chunk, values in zip(batch, vectors, strict=True):
            if not values:
                raise EmbeddingGenerationError("The embedding provider returned an empty vector.")
            result.append(Embedding(chunk_id=chunk.id, vector=[float(value) for value in values]))
        return result
