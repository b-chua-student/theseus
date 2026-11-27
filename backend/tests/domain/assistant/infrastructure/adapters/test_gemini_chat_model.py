"""Unit tests for the Gemini chat adapter's request check, using a fake client (no key needed)."""

from dataclasses import dataclass, field

import pytest
from google.genai import types

from domain.assistant.infrastructure.adapters.gemini_chat_model import ChatModels, GeminiChatModel
from domain.assistant.infrastructure.ports.token_counter import TokenCounter
from domain.assistant.models.errors import ChatRequestTooLargeError
from domain.assistant.models.value_objects import Query


@dataclass
class FakeModels:
    """Records generate calls and returns a fixed answer."""

    calls: list[list[types.Content]] = field(default_factory=list)

    def generate_content(
        self, *, model: str, contents: list[types.Content], config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        self.calls.append(contents)
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(content=types.Content(role="model", parts=[types.Part(text="Ok.")]))
            ]
        )


@dataclass
class FakeClient:
    fake: FakeModels = field(default_factory=FakeModels)

    @property
    def models(self) -> ChatModels:
        return self.fake


class OnePerCharacter(TokenCounter):
    def count(self, text: str) -> int:
        return len(text)


def test_a_request_within_the_window_is_sent() -> None:
    client = FakeClient()
    model = GeminiChatModel(client=client, token_counter=OnePerCharacter(), context_window=1000)

    answer = model.reply([], Query("Hello?"))

    assert answer.text == "Ok."
    assert len(client.fake.calls) == 1


def test_a_request_larger_than_the_window_is_refused_before_it_is_sent() -> None:
    client = FakeClient()
    model = GeminiChatModel(client=client, token_counter=OnePerCharacter(), context_window=5)

    with pytest.raises(ChatRequestTooLargeError):
        model.reply([], Query("This question is longer than five characters."))

    assert client.fake.calls == []


def test_the_check_counts_the_history_too() -> None:
    from domain.assistant.models.aggregates import Conversation
    from domain.assistant.models.value_objects import Answer, ProjectId

    conversation = Conversation.start(ProjectId.new())
    exchange = conversation.ask(Query("An earlier question"))
    conversation.answer(exchange.id, Answer("An earlier answer"))
    client = FakeClient()
    model = GeminiChatModel(client=client, token_counter=OnePerCharacter(), context_window=40)

    with pytest.raises(ChatRequestTooLargeError):
        model.reply(conversation.history, Query("Next?"))


def test_without_a_counter_or_window_nothing_is_checked() -> None:
    client = FakeClient()

    GeminiChatModel(client=client).reply([], Query("x" * 10_000))

    assert len(client.fake.calls) == 1
