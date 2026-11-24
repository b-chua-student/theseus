"""Unit tests for the Conversation aggregate and its value objects."""

import pytest

from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.errors import (
    EmptyAnswerError,
    EmptyQueryError,
    ExchangeAlreadyAnsweredError,
    ExchangeNotFoundError,
    PendingExchangeError,
)
from domain.assistant.models.value_objects import Answer, ExchangeId, ProjectId, Query


@pytest.fixture
def conversation() -> Conversation:
    return Conversation.start(ProjectId.new())


def test_new_conversation_is_empty_and_starts_on_web_alone(conversation: Conversation) -> None:
    assert conversation.exchanges == []
    assert conversation.pending is None
    assert conversation.history == []
    assert conversation.context_scope == "none"
    assert (conversation.web, conversation.manuscript) == (True, False)
    assert conversation.source_ids is None
    assert conversation.sources == []


def test_ask_opens_a_pending_exchange(conversation: Conversation) -> None:
    exchange = conversation.ask(Query("What is entropy?"))

    assert conversation.pending is exchange
    assert conversation.history == []


def test_ask_is_rejected_while_an_exchange_is_pending(conversation: Conversation) -> None:
    conversation.ask(Query("First?"))

    with pytest.raises(PendingExchangeError):
        conversation.ask(Query("Second?"))


def test_answer_completes_the_exchange_and_adds_it_to_history(conversation: Conversation) -> None:
    exchange = conversation.ask(Query("First?"))

    conversation.answer(exchange.id, Answer("Reply"))

    assert conversation.pending is None
    assert conversation.history == [exchange]
    assert exchange.answer == Answer("Reply")


def test_answer_raises_for_unknown_exchange(conversation: Conversation) -> None:
    conversation.ask(Query("First?"))

    with pytest.raises(ExchangeNotFoundError):
        conversation.answer(ExchangeId.new(), Answer("Reply"))


def test_answering_twice_is_rejected(conversation: Conversation) -> None:
    exchange = conversation.ask(Query("First?"))
    conversation.answer(exchange.id, Answer("Reply"))

    with pytest.raises(ExchangeAlreadyAnsweredError):
        conversation.answer(exchange.id, Answer("Another"))


def test_discard_pending_removes_only_the_unanswered_exchange(conversation: Conversation) -> None:
    answered = conversation.ask(Query("First?"))
    conversation.answer(answered.id, Answer("Reply"))
    conversation.ask(Query("Second?"))

    conversation.discard_pending()

    assert conversation.exchanges == [answered]
    conversation.ask(Query("Third?"))


def test_discard_pending_does_nothing_without_a_pending_exchange(
    conversation: Conversation,
) -> None:
    exchange = conversation.ask(Query("First?"))
    conversation.answer(exchange.id, Answer("Reply"))

    conversation.discard_pending()

    assert conversation.exchanges == [exchange]


def test_conversations_are_equal_by_id() -> None:
    project_id = ProjectId.new()

    assert Conversation.start(project_id) != Conversation.start(project_id)


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_blank_query_is_rejected(text: str) -> None:
    with pytest.raises(EmptyQueryError):
        Query(text)


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_blank_answer_is_rejected(text: str) -> None:
    with pytest.raises(EmptyAnswerError):
        Answer(text)


def test_query_and_answer_strip_surrounding_whitespace() -> None:
    assert Query("  hi  ").text == "hi"
    assert Answer("  yo  ").text == "yo"
