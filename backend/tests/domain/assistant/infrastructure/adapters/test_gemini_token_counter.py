"""Unit tests for the Gemini token counter, using a fake client (no API key needed)."""

from dataclasses import dataclass, field

from google.genai import types

from domain.assistant.infrastructure.adapters.gemini_token_counter import (
    CountModels,
    GeminiTokenCounter,
    estimate_tokens,
)


@dataclass
class FakeModels:
    """Records count calls and returns a scripted total or raises."""

    calls: list[str] = field(default_factory=list)
    total: int | None = 7
    error: Exception | None = None

    def count_tokens(self, *, model: str, contents: str) -> types.CountTokensResponse:
        self.calls.append(contents)
        if self.error is not None:
            raise self.error
        return types.CountTokensResponse(total_tokens=self.total)


@dataclass
class FakeClient:
    fake: FakeModels = field(default_factory=FakeModels)

    @property
    def models(self) -> CountModels:
        return self.fake


def test_counts_through_the_provider_and_caches_the_result() -> None:
    client = FakeClient()
    counter = GeminiTokenCounter(client=client)

    assert counter.count("some passage") == 7
    assert counter.count("some passage") == 7
    assert client.fake.calls == ["some passage"]


def test_empty_text_costs_nothing_and_is_not_sent() -> None:
    client = FakeClient()

    assert GeminiTokenCounter(client=client).count("") == 0
    assert client.fake.calls == []


def test_a_provider_failure_uses_a_high_estimate_and_is_not_cached() -> None:
    client = FakeClient(FakeModels(error=RuntimeError("offline")))
    counter = GeminiTokenCounter(client=client)
    text = "x" * 100

    assert counter.count(text) == estimate_tokens(text) == 51
    client.fake.error = None
    assert counter.count(text) == 7


def test_a_response_without_a_total_uses_the_estimate() -> None:
    client = FakeClient(FakeModels(total=None))

    assert GeminiTokenCounter(client=client).count("abcd") == estimate_tokens("abcd")
