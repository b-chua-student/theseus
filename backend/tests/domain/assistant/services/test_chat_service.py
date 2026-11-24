"""Unit tests for the assistant ChatService."""

from uuid import uuid4

import pytest

from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_embedding_generator import (
    InMemoryEmbeddingGenerator,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import InMemoryVectorStore
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.entities import Exchange
from domain.assistant.models.errors import (
    ChatModelError,
    ConversationNotFoundError,
    EmptyQueryError,
    InvalidConversationIdError,
    InvalidProjectIdError,
    PendingExchangeError,
)
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    ChunkId,
    ConversationId,
    DocumentRefId,
    ExchangeContext,
    IndexedDocumentTitle,
    ProjectId,
    Query,
    RetrievedChunk,
)
from domain.assistant.services.chat import ChatService


class FakeChatModel(ChatModel):
    """Chat model fake that records calls and returns a canned answer or raises."""

    def __init__(self, answer: str = "An answer.", error: Exception | None = None) -> None:
        self.answer = answer
        self.error = error
        self.calls: list[tuple[list[Exchange], Query, list[RetrievedChunk] | None]] = []
        self.drafts: list[str | None] = []
        self.quotes: list[str | None] = []

    def reply(
        self,
        history: list[Exchange],
        query: Query,
        context: list[RetrievedChunk] | None = None,
        manuscript_text: str | None = None,
        quote: str | None = None,
    ) -> Answer:
        self.calls.append((history, query, context))
        self.drafts.append(manuscript_text)
        self.quotes.append(quote)
        if self.error is not None:
            raise self.error
        return Answer(self.answer)


class Library:
    """Indexed sources for one project, wired to the in-memory retrieval adapters."""

    def __init__(self, project_id: str) -> None:
        self.project_id = ProjectId.from_str(project_id)
        self.documents = InMemoryIndexedDocumentRepository()
        self.vectors = InMemoryVectorStore()
        self.embedder = InMemoryEmbeddingGenerator()
        self.active: list[DocumentRefId] = []

    def add_source(
        self,
        text: str,
        *,
        indexed: bool = True,
        active: bool = True,
        title: str = "Source",
        more_passages: int = 0,
    ) -> DocumentRefId:
        ref = DocumentRefId.new()
        document = IndexedDocument.create(IndexedDocumentTitle(title), ref, self.project_id)
        if indexed:
            chunks = [
                Chunk(
                    id=ChunkId.new(),
                    text=text if index == 0 else f"{text} {index}",
                    position=str(index + 1),
                    location=f"p{index + 1}",
                    content_hash=f"{text}{index}",
                )
                for index in range(more_passages + 1)
            ]
            document.start_indexing()
            document.complete_indexing(chunks)
            self.vectors.upsert(ref, self.embedder.generate(chunks), chunks)
        self.documents.add(document)
        if active:
            self.active.append(ref)
        return ref


@pytest.fixture
def project_id() -> str:
    return str(uuid4())


@pytest.fixture
def repository() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()


@pytest.fixture
def model() -> FakeChatModel:
    return FakeChatModel()


@pytest.fixture
def service(repository: InMemoryConversationRepository, model: FakeChatModel) -> ChatService:
    return ChatService(repository, model)


@pytest.fixture
def library(project_id: str) -> Library:
    return Library(project_id)


@pytest.fixture
def retrieving_service(
    repository: InMemoryConversationRepository, model: FakeChatModel, library: Library
) -> ChatService:
    return ChatService(
        repository,
        model,
        embedding_generator=library.embedder,
        vector_store=library.vectors,
        document_repository=library.documents,
        source_ids=lambda _project: list(library.active),
    )


def test_start_creates_and_stores_an_empty_conversation(
    service: ChatService, project_id: str
) -> None:
    conversation_id = service.start(project_id)

    conversation = service.get(project_id, str(conversation_id.value))
    assert conversation.exchanges == []
    assert conversation.project_id == ProjectId.from_str(project_id)


def test_start_rejects_an_invalid_project_id(service: ChatService) -> None:
    with pytest.raises(InvalidProjectIdError):
        service.start("not-a-uuid")


def test_list_returns_only_conversations_of_the_project(
    service: ChatService, project_id: str
) -> None:
    mine = service.start(project_id)
    service.start(str(uuid4()))

    listed = service.list(project_id)

    assert [c.id for c in listed] == [mine]


def test_list_orders_most_recently_active_first(service: ChatService, project_id: str) -> None:
    older = service.start(project_id)
    newer = service.start(project_id)
    service.ask(str(older.value), "Question", context_scope="none")

    assert [c.id for c in service.list(project_id)][0] == older
    assert {c.id for c in service.list(project_id)} == {older, newer}


def test_get_raises_when_conversation_belongs_to_another_project(
    service: ChatService, project_id: str
) -> None:
    conversation_id = service.start(project_id)

    with pytest.raises(ConversationNotFoundError):
        service.get(str(uuid4()), str(conversation_id.value))


def test_get_raises_for_unknown_conversation(service: ChatService, project_id: str) -> None:
    with pytest.raises(ConversationNotFoundError):
        service.get(project_id, str(uuid4()))


def test_get_rejects_an_invalid_conversation_id(service: ChatService, project_id: str) -> None:
    with pytest.raises(InvalidConversationIdError):
        service.get(project_id, "nope")


def test_ask_returns_and_records_the_answer(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    model.answer = "  Paris.  "
    conversation_id = str(service.start(project_id).value)

    answer = service.ask(conversation_id, "  Capital of France?  ", context_scope="none")

    assert answer == Answer("Paris.")
    [exchange] = service.get(project_id, conversation_id).history
    assert exchange.query.text == "Capital of France?"
    assert exchange.answer == Answer("Paris.")


def test_ask_passes_earlier_answered_exchanges_as_history(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)
    service.ask(conversation_id, "First?", context_scope="none")

    service.ask(conversation_id, "Second?", context_scope="none")

    first_history, _, _ = model.calls[0]
    second_history, second_query, _ = model.calls[1]
    assert first_history == []
    assert [e.query.text for e in second_history] == ["First?"]
    assert second_query == Query("Second?")


def test_ask_raises_for_unknown_conversation(service: ChatService) -> None:
    with pytest.raises(ConversationNotFoundError):
        service.ask(str(uuid4()), "Hello?", context_scope="none")


def test_ask_raises_when_project_does_not_own_the_conversation(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    with pytest.raises(ConversationNotFoundError):
        service.ask(conversation_id, "Hello?", context_scope="none", project_id=str(uuid4()))

    assert model.calls == []


def test_ask_rejects_a_blank_question_without_calling_the_model(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    with pytest.raises(EmptyQueryError):
        service.ask(conversation_id, "   ", context_scope="none")

    assert model.calls == []


def test_ask_rejects_an_unsupported_context_scope(service: ChatService, project_id: str) -> None:
    conversation_id = str(service.start(project_id).value)

    with pytest.raises(ValueError, match="context scope"):
        service.ask(conversation_id, "Hi?", context_scope="web")  # type: ignore[arg-type]


def test_ask_records_scope_and_selected_sources_on_the_conversation(
    service: ChatService, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)
    source_id = str(uuid4())

    service.ask(conversation_id, "Hi?", context_scope="none", source_ids=[source_id])

    conversation = service.get(project_id, conversation_id)
    assert conversation.context_scope == "none"
    assert conversation.source_ids == [source_id]


def test_ask_with_manuscript_scope_passes_the_manuscript_apart_from_the_question(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    service.ask(
        conversation_id,
        "Summarise it",
        context_scope="manuscript",
        manuscript_text="  Chapter one text.  ",
    )

    [(_, query, context)] = model.calls
    assert query == Query("Summarise it")
    assert model.drafts == ["  Chapter one text.  "]
    assert context == []


def test_ask_with_an_empty_manuscript_still_passes_the_empty_draft(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    service.ask(conversation_id, "Summarise it", context_scope="manuscript")

    assert model.drafts == [""]


def test_ask_with_none_scope_sends_the_plain_question_and_no_context(
    retrieving_service: ChatService,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    library.add_source("Relevant passage")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(
        conversation_id, "Question?", context_scope="none", manuscript_text="ignored"
    )

    [(_, query, context)] = model.calls
    assert query == Query("Question?")
    assert context == []


def test_ask_with_source_library_scope_sends_retrieved_chunks(
    retrieving_service: ChatService,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    library.add_source("Relevant passage")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(conversation_id, "Question?")

    [(_, query, context)] = model.calls
    assert query == Query("Question?")
    assert context is not None
    assert [c.text for c in context] == ["Relevant passage"]


def test_ask_retrieval_is_limited_to_the_selected_sources(
    retrieving_service: ChatService,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    library.add_source("Passage A")
    selected = library.add_source("Passage B")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(conversation_id, "Question?", source_ids=[str(selected.value)])

    context = model.calls[0][2]
    assert context is not None
    assert [c.text for c in context] == ["Passage B"]


def test_ask_retrieval_skips_sources_that_are_not_active_or_not_indexed(
    retrieving_service: ChatService,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    library.add_source("Removed source", active=False)
    library.add_source("Unindexed source", indexed=False)
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(conversation_id, "Question?")

    assert model.calls[0][2] == []


def test_ask_retrieval_respects_top_k(
    repository: InMemoryConversationRepository,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    for index in range(4):
        library.add_source(f"Passage {index}")
    service = ChatService(
        repository,
        model,
        embedding_generator=library.embedder,
        vector_store=library.vectors,
        document_repository=library.documents,
        top_k=2,
        source_ids=lambda _project: list(library.active),
    )
    conversation_id = str(service.start(project_id).value)

    service.ask(conversation_id, "Question?")

    context = model.calls[0][2]
    assert context is not None
    assert len(context) == 2


def test_ask_without_retrieval_adapters_answers_with_no_context(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    service.ask(conversation_id, "Question?")

    assert model.calls[0][2] == []


def test_ask_answers_without_context_when_retrieval_fails(
    repository: InMemoryConversationRepository,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    class BrokenVectorStore(InMemoryVectorStore):
        def query(self, *args: object, **kwargs: object) -> list[RetrievedChunk]:
            raise RuntimeError("vector store down")

    library.add_source("Passage")
    service = ChatService(
        repository,
        model,
        embedding_generator=library.embedder,
        vector_store=BrokenVectorStore(),
        document_repository=library.documents,
        source_ids=lambda _project: list(library.active),
    )
    conversation_id = str(service.start(project_id).value)

    answer = service.ask(conversation_id, "Question?")

    assert answer == Answer("An answer.")
    assert model.calls[0][2] == []


def test_ask_reraises_model_errors_and_discards_the_exchange(
    repository: InMemoryConversationRepository, project_id: str
) -> None:
    model = FakeChatModel(error=ChatModelError("provider outage"))
    service = ChatService(repository, model)
    conversation_id = str(service.start(project_id).value)

    with pytest.raises(ChatModelError, match="provider outage"):
        service.ask(conversation_id, "Question?", context_scope="none")

    assert service.get(project_id, conversation_id).exchanges == []


def test_ask_wraps_unexpected_model_failures_in_chat_model_error(
    repository: InMemoryConversationRepository, project_id: str
) -> None:
    model = FakeChatModel(error=RuntimeError("boom"))
    service = ChatService(repository, model)
    conversation_id = str(service.start(project_id).value)

    with pytest.raises(ChatModelError) as raised:
        service.ask(conversation_id, "Question?", context_scope="none")

    assert isinstance(raised.value.__cause__, RuntimeError)
    assert service.get(project_id, conversation_id).exchanges == []


def test_user_can_retry_after_a_model_failure(
    repository: InMemoryConversationRepository, project_id: str
) -> None:
    model = FakeChatModel(error=ChatModelError("provider outage"))
    service = ChatService(repository, model)
    conversation_id = str(service.start(project_id).value)
    with pytest.raises(ChatModelError):
        service.ask(conversation_id, "Question?", context_scope="none")

    model.error = None
    answer = service.ask(conversation_id, "Question?", context_scope="none")

    assert answer == Answer("An answer.")


def test_ask_rejects_a_question_while_a_previous_one_is_pending(
    service: ChatService, repository: InMemoryConversationRepository, project_id: str
) -> None:
    conversation_id = service.start(project_id)
    conversation = repository.get(ConversationId(conversation_id.value))
    assert conversation is not None
    conversation.ask(Query("Unanswered"))

    with pytest.raises(PendingExchangeError):
        service.ask(str(conversation_id.value), "Next?", context_scope="none")


def test_ask_with_a_combined_context_sends_the_draft_and_retrieved_passages(
    retrieving_service: ChatService,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    selected = library.add_source("Methods reports 18 participants.")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(
        conversation_id,
        "Which studies support my figure?",
        context_scope="source_library",
        source_ids=[str(selected.value)],
        manuscript_text="The trial enrolled 18 participants.",
    )

    [(_, query, context)] = model.calls
    assert query == Query("Which studies support my figure?")
    assert model.drafts == ["The trial enrolled 18 participants."]
    assert context is not None
    assert [c.text for c in context] == ["Methods reports 18 participants."]


def test_ask_passes_the_quote_apart_from_the_question_and_without_the_draft(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    service.ask(
        conversation_id,
        "How does this compare?",
        context_scope="none",
        quote="Children recovered in 5 days",
    )

    [(_, query, _)] = model.calls
    assert query == Query("How does this compare?")
    assert model.quotes == ["Children recovered in 5 days"]
    assert model.drafts == [None]


def test_ask_accepts_a_decoded_context(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    conversation_id = str(service.start(project_id).value)

    service.ask(
        conversation_id,
        "Summarise it",
        context=ExchangeContext.decode("manuscript", manuscript_text="Chapter one."),
    )

    assert model.drafts == ["Chapter one."]
    assert service.get(project_id, conversation_id).context_scope == "manuscript"


def test_ask_retrieval_labels_each_passage_with_its_source_id_and_title(
    model: FakeChatModel, library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    methods = library.add_source("Methods text", title="Methods")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(conversation_id, "Question?")

    context = model.calls[0][2]
    assert context is not None
    assert [(chunk.doc_ref_id, chunk.title) for chunk in context] == [(methods, "Methods")]


def test_ask_retrieval_searches_each_source_on_its_own(
    model: FakeChatModel, library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    refs = [library.add_source(f"Text {index}", title=f"S{index}") for index in range(3)]
    searched: list[list[DocumentRefId] | None] = []
    original = library.vectors.query

    def recording_query(
        vector: list[float], k: int = 5, doc_ref_ids: list[DocumentRefId] | None = None
    ) -> list[RetrievedChunk]:
        searched.append(doc_ref_ids)
        return original(vector, k, doc_ref_ids)

    library.vectors.query = recording_query  # type: ignore[method-assign,assignment]
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(conversation_id, "Question?")

    assert sorted(searched, key=str) == sorted([[ref] for ref in refs], key=str)


def test_ask_retrieval_lets_a_source_with_many_matches_share_with_another(
    repository: InMemoryConversationRepository,
    model: FakeChatModel,
    library: Library,
    project_id: str,
) -> None:
    many = library.add_source("Sample size", title="Methods", more_passages=4)
    one = library.add_source("Sample size", title="Replication")
    service = ChatService(
        repository,
        model,
        embedding_generator=library.embedder,
        vector_store=library.vectors,
        document_repository=library.documents,
        top_k=2,
        source_ids=lambda _project: list(library.active),
    )
    conversation_id = str(service.start(project_id).value)

    service.ask(conversation_id, "Sample size")

    context = model.calls[0][2]
    assert context is not None
    assert {chunk.doc_ref_id for chunk in context} == {many, one}


def test_ask_retrieval_uses_the_quote_with_the_question_to_find_passages(
    model: FakeChatModel, library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    library.add_source("Children recovered in 7 days", title="Methods")
    library.add_source("Unrelated words", title="Other")
    embedded: list[str] = []
    original = library.embedder.generate

    def recording_generate(chunks: list[Chunk]) -> list:  # type: ignore[type-arg]
        embedded.extend(chunk.text for chunk in chunks)
        return original(chunks)

    library.embedder.generate = recording_generate  # type: ignore[method-assign]
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(
        conversation_id,
        "How does this compare?",
        context=ExchangeContext.decode("source_library", quote="Children recovered in 5 days"),
    )

    assert embedded == ["Children recovered in 5 days\nHow does this compare?"]


def test_ask_resolves_cited_keys_against_the_supplied_excerpts(
    model: FakeChatModel, library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    methods = library.add_source("Methods text", title="Methods")
    model.answer = "Methods supports it [1]. Nothing backs [7] or [1] again."
    conversation_id = str(retrieving_service.start(project_id).value)

    answer = retrieving_service.ask(conversation_id, "Question?")

    assert [(c.key, c.doc_ref_id, c.title) for c in answer.citations] == [("1", methods, "Methods")]


def test_ask_cites_nothing_when_no_excerpt_was_supplied(
    service: ChatService, model: FakeChatModel, project_id: str
) -> None:
    model.answer = "General knowledge [1]."
    conversation_id = str(service.start(project_id).value)

    answer = service.ask(conversation_id, "Question?", context_scope="none")

    assert answer.citations == ()


def test_ask_saves_the_selection_after_a_successful_exchange(
    library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    methods = library.add_source("Methods text", title="Methods")
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(
        conversation_id,
        "Question?",
        context=ExchangeContext.decode(
            "source_library",
            manuscript_text="Draft",
            source_ids=[str(methods.value)],
            web=False,
            manuscript=True,
        ),
    )

    saved = retrieving_service.get(project_id, conversation_id)
    assert (saved.web, saved.manuscript) == (False, True)
    assert saved.source_ids == [str(methods.value)]
    assert [(s.id, s.title) for s in saved.sources] == [(str(methods.value), "Methods")]


def test_ask_keeps_the_previous_selection_when_the_exchange_fails(
    repository: InMemoryConversationRepository,
    library: Library,
    project_id: str,
) -> None:
    methods = library.add_source("Methods text", title="Methods")
    model = FakeChatModel()
    service = ChatService(
        repository,
        model,
        embedding_generator=library.embedder,
        vector_store=library.vectors,
        document_repository=library.documents,
        source_ids=lambda _project: list(library.active),
    )
    conversation_id = str(service.start(project_id).value)
    service.ask(
        conversation_id,
        "First?",
        context=ExchangeContext.decode("source_library", source_ids=[str(methods.value)], web=True),
    )
    model.error = ChatModelError("down")

    with pytest.raises(ChatModelError):
        service.ask(conversation_id, "Second?", context=ExchangeContext.decode("none"))

    saved = service.get(project_id, conversation_id)
    assert saved.web is True
    assert saved.source_ids == [str(methods.value)]
    assert [s.title for s in saved.sources] == ["Methods"]


def test_ask_never_stores_the_title_of_a_source_from_another_project(
    model: FakeChatModel, library: Library, retrieving_service: ChatService, project_id: str
) -> None:
    foreign = DocumentRefId.new()
    library.documents.add(
        IndexedDocument.create(IndexedDocumentTitle("Secret title"), foreign, ProjectId.new())
    )
    conversation_id = str(retrieving_service.start(project_id).value)

    retrieving_service.ask(
        conversation_id,
        "Question?",
        context=ExchangeContext.decode("source_library", source_ids=[str(foreign.value)]),
    )

    saved = retrieving_service.get(project_id, conversation_id)
    assert [s.title for s in saved.sources] == [""]
