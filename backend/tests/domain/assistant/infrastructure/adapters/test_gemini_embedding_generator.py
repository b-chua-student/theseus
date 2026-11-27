"""Unit tests for the Gemini embedding adapter, using a fake client (no API key needed)."""

from dataclasses import dataclass, field

import pytest
from google.genai import errors as genai_errors
from google.genai import types

from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
    MAX_BATCH_SIZE,
    EmbeddingModels,
    GeminiEmbeddingGenerator,
)
from domain.assistant.models.errors import EmbeddingGenerationError
from domain.assistant.models.value_objects import Chunk, ChunkId


@dataclass
class FakeModels:
    """Records embed calls and returns one vector per input, or a scripted response."""

    calls: list[tuple[str, list[str]]] = field(default_factory=list)
    response: types.EmbedContentResponse | None = None
    error: Exception | None = None

    def embed_content(
        self, *, model: str, contents: list[str], config: types.EmbedContentConfig
    ) -> types.EmbedContentResponse:
        self.calls.append((model, list(contents)))
        if self.error is not None:
            raise self.error
        if self.response is not None:
            return self.response
        return types.EmbedContentResponse(
            embeddings=[types.ContentEmbedding(values=[float(len(text)), 1.0]) for text in contents]
        )


@dataclass
class FakeClient:
    fake: FakeModels = field(default_factory=FakeModels)

    @property
    def models(self) -> EmbeddingModels:
        return self.fake


def chunk(text: str) -> Chunk:
    return Chunk(id=ChunkId.new(), text=text, position="1", location="p1", content_hash=text)


def test_returns_one_embedding_per_chunk_in_order() -> None:
    client = FakeClient()
    chunks = [chunk("a"), chunk("bbb")]

    embeddings = GeminiEmbeddingGenerator(client=client, model="test-model").generate(chunks)

    assert [e.chunk_id for e in embeddings] == [c.id for c in chunks]
    assert [e.vector for e in embeddings] == [[1.0, 1.0], [3.0, 1.0]]
    assert client.fake.calls == [("test-model", ["a", "bbb"])]


def test_batches_large_inputs() -> None:
    client = FakeClient()
    chunks = [chunk(f"text {index}") for index in range(MAX_BATCH_SIZE + 1)]

    embeddings = GeminiEmbeddingGenerator(client=client).generate(chunks)

    assert len(embeddings) == MAX_BATCH_SIZE + 1
    assert [len(contents) for _, contents in client.fake.calls] == [MAX_BATCH_SIZE, 1]


def test_empty_input_makes_no_request() -> None:
    client = FakeClient()

    assert GeminiEmbeddingGenerator(client=client).generate([]) == []
    assert client.fake.calls == []


def test_rejects_a_response_with_the_wrong_number_of_vectors() -> None:
    client = FakeClient(FakeModels(response=types.EmbedContentResponse(embeddings=[])))

    with pytest.raises(EmbeddingGenerationError):
        GeminiEmbeddingGenerator(client=client).generate([chunk("a")])


def test_rejects_an_empty_vector() -> None:
    response = types.EmbedContentResponse(embeddings=[types.ContentEmbedding(values=[])])
    client = FakeClient(FakeModels(response=response))

    with pytest.raises(EmbeddingGenerationError):
        GeminiEmbeddingGenerator(client=client).generate([chunk("a")])


@pytest.mark.parametrize(
    "error",
    [genai_errors.APIError(503, {"error": {"message": "unavailable"}}), TimeoutError("slow")],
)
def test_wraps_provider_failures(error: Exception) -> None:
    client = FakeClient(FakeModels(error=error))

    with pytest.raises(EmbeddingGenerationError):
        GeminiEmbeddingGenerator(client=client).generate([chunk("a")])


def test_requires_an_api_key_without_a_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(
        "domain.assistant.infrastructure.adapters.gemini_embedding_generator.load_dotenv",
        lambda: None,
    )

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiEmbeddingGenerator()
