"""Unit tests for the MongoDB conversation repository, with a mocked collection."""

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
    SelectedSource,
)


def make_repository() -> tuple[MongoConversationRepository, MagicMock]:
    """Create a repository with a mocked MongoDB collection."""
    database = MagicMock()
    return MongoConversationRepository(database), database.__getitem__.return_value


def _saved_document(conversation: Conversation) -> dict:
    repository, collection = make_repository()
    repository.save(conversation)
    return collection.replace_one.call_args.args[1]


def test_saves_the_web_and_manuscript_flags_and_the_selected_sources() -> None:
    conversation = Conversation.start(ProjectId.new())
    conversation.context_scope = "source_library"
    conversation.web = False
    conversation.manuscript = True
    conversation.source_ids = ["a", "b"]
    conversation.sources = [SelectedSource("a", "Methods"), SelectedSource("b", "Replication")]

    doc = _saved_document(conversation)

    assert doc["web"] is False
    assert doc["manuscript"] is True
    assert doc["source_ids"] == ["a", "b"]
    assert doc["sources"] == [
        {"id": "a", "title": "Methods"},
        {"id": "b", "title": "Replication"},
    ]


def test_loads_the_saved_selection() -> None:
    repository, collection = make_repository()
    conversation = Conversation.start(ProjectId.new())
    conversation.web = False
    conversation.manuscript = True
    conversation.sources = [SelectedSource("a", "Methods")]
    collection.find_one.return_value = _saved_document(conversation)

    loaded = repository.get(conversation.id)

    assert loaded is not None
    assert (loaded.web, loaded.manuscript) == (False, True)
    assert loaded.sources == [SelectedSource("a", "Methods")]


def _legacy_document(scope: str | None, source_ids: list[str] | None) -> dict:
    doc = _saved_document(Conversation.start(ProjectId.new()))
    for key in ("web", "manuscript", "sources", "context_scope"):
        doc.pop(key)
    if scope is not None:
        doc["context_scope"] = scope
    doc["source_ids"] = source_ids
    return doc


def _load(doc: dict) -> Conversation:
    repository, collection = make_repository()
    collection.find_one.return_value = doc
    loaded = repository.get(Conversation.start(ProjectId.new()).id)
    assert loaded is not None
    return loaded


def test_a_legacy_none_record_loads_as_web_alone() -> None:
    loaded = _load(_legacy_document("none", None))

    assert (loaded.web, loaded.manuscript, loaded.sources) == (True, False, [])


def test_a_legacy_manuscript_record_loads_as_manuscript_alone() -> None:
    loaded = _load(_legacy_document("manuscript", None))

    assert (loaded.web, loaded.manuscript) == (False, True)


def test_a_legacy_source_library_record_loads_as_its_sources_alone() -> None:
    loaded = _load(_legacy_document("source_library", ["a"]))

    assert (loaded.web, loaded.manuscript, loaded.source_ids) == (False, False, ["a"])


def test_a_legacy_all_library_record_keeps_a_null_source_list() -> None:
    loaded = _load(_legacy_document(None, None))

    assert loaded.context_scope == "source_library"
    assert loaded.source_ids is None


def answered_conversation(citations: tuple[Citation, ...]) -> Conversation:
    conversation = Conversation.start(ProjectId.new())
    exchange = conversation.ask(Query("When did it start?"))
    conversation.answer(exchange.id, Answer("It started in May [1].", citations=citations))
    return conversation


def test_s101_citations_survive_a_save_and_load() -> None:
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
