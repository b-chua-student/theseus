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
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    ChunkId,
    DocumentRefId,
    IndexedDocumentTitle,
    ProjectId,
)
from domain.assistant.services.chat import ChatService


class RecordingModel(ChatModel):
    def __init__(self) -> None:
        self.context = None

    def reply(self, history, query, context=None):
        self.context = context
        return Answer("ok")


def _index(docs, store, emb, project_id, text, *, searchable=True) -> None:
    doc = IndexedDocument.create(IndexedDocumentTitle("d"), DocumentRefId.new(), project_id)
    chunk = Chunk(ChunkId.new(), text, "0", "p1", "h")
    if searchable:
        doc.start_indexing()
        doc.complete_indexing([chunk])
        store.upsert(doc.doc_ref_id, emb.generate([chunk]), [chunk])
    docs.add(doc)


def _service(model):
    docs, store, emb = (
        InMemoryIndexedDocumentRepository(),
        InMemoryVectorStore(),
        InMemoryEmbeddingGenerator(),
    )
    svc = ChatService(
        InMemoryConversationRepository(),
        model,
        emb,
        store,
        docs,
        top_k=1,
        source_ids=lambda project: [doc.doc_ref_id for doc in docs.list_by_project(project)],
    )
    return svc, docs, store, emb


def test_ask_passes_top_k_context_scoped_to_project() -> None:
    model = RecordingModel()
    svc, docs, store, emb = _service(model)
    mine, other = ProjectId.new(), ProjectId.new()
    _index(docs, store, emb, mine, "the question text")
    _index(docs, store, emb, other, "the question text")
    cid = svc.start(str(mine.value))
    svc.ask(str(cid.value), "the question text")
    assert model.context is not None
    assert len(model.context) == 1
    assert model.context[0].text == "the question text"
    assert docs.list_by_project(mine)[0].doc_ref_id == model.context[0].doc_ref_id


def test_ask_without_searchable_docs_has_empty_context() -> None:
    model = RecordingModel()
    svc, docs, store, emb = _service(model)
    p = ProjectId.new()
    _index(docs, store, emb, p, "x", searchable=False)
    svc.ask(str(svc.start(str(p.value)).value), "hello")
    assert model.context == []


def test_none_skips_retrieval_even_with_indexed_documents() -> None:
    model = RecordingModel()
    svc, docs, store, emb = _service(model)
    project = ProjectId.new()
    _index(docs, store, emb, project, "library content")
    svc._retrieve = lambda *_: (_ for _ in ()).throw(AssertionError("retrieval called"))
    svc.ask(str(svc.start(str(project.value)).value), "hello", context_scope="none")
    assert model.context == []


def test_source_library_excludes_manuscripts_and_removed_sources() -> None:
    from bootstrap.container import build_container
    from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
        InMemorySourceRepository,
    )
    from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus
    from domain.src_lib.models.aggregates import Source
    from domain.src_lib.models.value_objects import SourceTitle, TextBody

    model = RecordingModel()
    sources = InMemorySourceRepository()
    events = InProcessEventBus()
    container = build_container(chat_model=model, source_repo=sources, publisher=events)
    project = ProjectId.new()
    source = Source.add(
        SourceTitle("Library source"),
        "",
        project.value,
        kind="text",
        content=TextBody("Unique library content"),
    )
    sources.save(source)
    events.publish(source.pull_events())
    assistant = container.assistant
    _index(
        assistant.indexed_document_repository,
        assistant.vector_store,
        assistant.embedding_generator,
        project,
        "manuscript content",
    )
    chat = assistant.chat
    assert chat is not None
    cid = str(chat.start(str(project.value)).value)
    chat.ask(cid, "Unique library content", context_scope="source_library")
    assert model.context and len(model.context) == 1
    assert model.context[0].text == "Unique library content"
    container.source.remove.execute(str(source.id.value))
    chat.ask(cid, "Unique library content", context_scope="source_library")
    assert model.context == []


def test_context_scope_validation() -> None:
    import pytest
    from pydantic import ValidationError

    from domain.assistant.api.requests import AskRequest

    assert AskRequest(query="hello", context_scope="none").context_scope == "none"
    assert AskRequest(query="hello").context_scope == "source_library"
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "hello", "context_scope": "manuscript"})
