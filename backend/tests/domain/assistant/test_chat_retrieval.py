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
    svc = ChatService(InMemoryConversationRepository(), model, emb, store, docs, top_k=1)
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
