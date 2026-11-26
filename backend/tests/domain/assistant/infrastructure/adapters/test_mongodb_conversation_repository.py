"""Unit tests for the MongoDB conversation repository, with the collection mocked."""

from unittest.mock import MagicMock

from domain.assistant.infrastructure.adapters.mongodb_conversation_repository import (
    MongoConversationRepository,
)
from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.value_objects import (
    Answer,
    ChunkId,
    Citation,
    DocumentRefId,
    ProjectId,
    Query,
)


def make_repository() -> tuple[MongoConversationRepository, MagicMock]:
    database = MagicMock()
    return MongoConversationRepository(database), database.__getitem__.return_value


def answered_conversation(citations: tuple[Citation, ...]) -> Conversation:
    conversation = Conversation.start(ProjectId.new())
    exchange = conversation.ask(Query("When did it start?"))
    conversation.answer(exchange.id, Answer("It started in May [1].", citations=citations))
    return conversation


def test_s004_citations_survive_a_save_and_load() -> None:
    repository, collection = make_repository()
    citation = Citation(1, ChunkId.new(), DocumentRefId.new(), "P1")
    conversation = answered_conversation((citation,))

    repository.save(conversation)
    collection.find_one.return_value = collection.replace_one.call_args.args[1]
    loaded = repository.get(conversation.id)

    assert loaded is not None
    [exchange] = loaded.exchanges
    assert exchange.answer is not None
    assert exchange.answer.citations == (citation,)


def test_an_exchange_stored_before_citations_existed_loads_without_sources() -> None:
    repository, collection = make_repository()
    conversation = answered_conversation(())
    repository.save(conversation)
    stored = collection.replace_one.call_args.args[1]
    del stored["exchanges"][0]["citations"]
    collection.find_one.return_value = stored

    loaded = repository.get(conversation.id)

    assert loaded is not None
    assert loaded.exchanges[0].answer == Answer("It started in May [1].")
    assert loaded.exchanges[0].answer.citations == ()  # type: ignore[union-attr]
