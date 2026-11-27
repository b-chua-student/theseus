"""Production RAG acceptance tests. Model provisioning precedes the offline test boundary."""

import hashlib
import socket
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock, Mock
from uuid import UUID, uuid4

import pytest
from huggingface_hub import snapshot_download
from tokenizers import Tokenizer

from bootstrap.app import create_app
from bootstrap.container import Container, build_container
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_document_chunker import (
    InMemoryDocumentChunker,
)
from domain.assistant.infrastructure.adapters.in_memory_embedding_generator import (
    InMemoryEmbeddingGenerator,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import InMemoryVectorStore
from domain.assistant.infrastructure.adapters.onnx_embedding_generator import OnnxEmbeddingGenerator
from domain.assistant.infrastructure.adapters.token_window_chunker import TokenWindowChunker
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    DocumentRefId,
    IndexStatus,
    ProjectId,
)
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.infrastructure.adapters.in_process_event_bus import InProcessEventBus

pytestmark = pytest.mark.integration
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BIKE = "Bicycle maintenance: patch the punctured inner tube and inflate the tire."
BREAD = "Baking sourdough: knead the dough and let it rise before heating the oven."
QUESTION = "How can I fix a flat on my bike?"


@pytest.fixture(scope="session")
def model_snapshot() -> Path:
    # Only provisioning may access the network. The same pinned files serve local and CI runs.
    files = ["tokenizer.json", "onnx/model.onnx"]
    snapshot = Path(
        snapshot_download(
            "sentence-transformers/all-MiniLM-L6-v2", revision=REVISION, allow_patterns=files
        )
    )
    for name in files:
        assert (snapshot / name).is_file(), f"Missing MiniLM artifact: {name}"
    return snapshot


@pytest.fixture(autouse=True)
def offline(model_snapshot, tmp_path, monkeypatch) -> Iterator[None]:
    attempts = []

    def deny(*args: object, **kwargs: object) -> None:
        attempts.append("network attempt")
        raise AssertionError("Network access during a RAG scenario")

    for target, name in [
        (socket, "getaddrinfo"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "sendto"),
    ]:
        monkeypatch.setattr(target, name, deny)
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("HF_HUB_OFFLINE", "1")
    monkeypatch.setenv("ANONYMIZED_TELEMETRY", "FALSE")
    monkeypatch.setenv("RAG_MODEL_PATH", str(model_snapshot))
    monkeypatch.setenv("RAG_VECTOR_PATH", str(tmp_path / "vectors"))
    monkeypatch.setattr("bootstrap.app.load_dotenv", lambda: None)
    monkeypatch.setattr("bootstrap.mongo.load_dotenv", lambda: None)
    monkeypatch.chdir(tmp_path)
    yield
    assert not attempts, "A network call was attempted, even if the caller caught its error"


@pytest.fixture
def chat_model() -> Mock:
    model = Mock()
    model.reply.return_value = Answer("Offline answer")
    return model


@pytest.fixture
def production(monkeypatch, chat_model) -> Callable[[], Container]:
    # Keep the same source and index metadata across app instances. Exercise the real
    # production composition root and vector store while replacing external Mongo I/O.
    monkeypatch.setattr("bootstrap.mongo.create_database", MagicMock())
    monkeypatch.setattr("bootstrap.app._build_chat_model", lambda: chat_model)
    adapters = "domain.assistant.infrastructure.adapters"
    for target, repo in [
        (
            "domain.identity.infrastructure.adapters.mongodb_identity_repository.MongoIdentityRepository",
            Mock(),
        ),
        (
            "domain.src_lib.infrastructure.adapters.mongodb_source_repository.MongoSourceRepository",
            InMemorySourceRepository(),
        ),
        (
            f"{adapters}.mongodb_indexed_document_repository.MongoIndexedDocumentRepository",
            InMemoryIndexedDocumentRepository(),
        ),
        (
            f"{adapters}.mongodb_conversation_repository.MongoConversationRepository",
            InMemoryConversationRepository(),
        ),
    ]:
        monkeypatch.setattr(target, Mock(return_value=repo))

    def start() -> Container:
        app = create_app({"MONGODB_URI": "mongodb://unused.invalid", "SECRET_KEY": "offline"})
        return app.extensions["container"]

    return start


@pytest.fixture(params=["adapters", "startup"])
def rag_container(request, production, model_snapshot, chat_model) -> Container:
    if request.param == "startup":
        return production()
    return build_container(
        document_chunker=TokenWindowChunker(model_snapshot),
        embedding_generator=OnnxEmbeddingGenerator(model_snapshot),
        chat_model=chat_model,
    )


def add(container: Container, project: UUID, text: str) -> DocumentRefId:
    source = container.source.add_text.execute("Test passage", text, project)
    return DocumentRefId(source.value)


def ask(
    container: Container, project: UUID, model: Mock, question: str = QUESTION
) -> list[DocumentRefId]:
    chat = container.assistant.chat
    assert chat is not None
    conversation = chat.start(str(project))
    chat.ask(str(conversation.value), question)
    return [hit.doc_ref_id for hit in model.reply.call_args.args[2]]


def test_s019_token_windows(rag_container, model_snapshot) -> None:
    chunker = rag_container.assistant.document_chunker
    tokenizer = Tokenizer.from_file(str(model_snapshot / "tokenizer.json"))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    text = (
        "Riders check the tire before every trip. " * 30
        + "\n\n"
        + "Bakers warm the oven before the dough is ready. " * 20
    ).strip()
    ids = tokenizer.encode(text, add_special_tokens=False).ids
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    recovered: list[int] = []
    for position, chunk in enumerate(chunks):
        tokens = tokenizer.encode(chunk.text, add_special_tokens=False).ids
        assert 0 < len(tokens) <= 192
        assert chunk.position == str(position)
        assert chunk.content_hash == hashlib.sha256(chunk.text.encode()).hexdigest()
        if position:
            assert tokens[:32] == recovered[-32:]
        recovered.extend(tokens[32:] if position else tokens)
    assert recovered == ids


def test_s020_embeddings_preserve_order(rag_container) -> None:
    assistant = rag_container.assistant
    chunks = assistant.document_chunker.chunk(BIKE) + assistant.document_chunker.chunk(BREAD)
    generator = assistant.embedding_generator
    embeddings = generator.generate(chunks)
    assert [e.chunk_id for e in embeddings] == [c.id for c in chunks]
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        assert len(embedding.vector) == 384
        assert embedding.vector == pytest.approx(generator.generate([chunk])[0].vector, abs=1e-5)


def test_s021_search_after_restart(production, chat_model, tmp_path) -> None:
    project = uuid4()
    source = add(production(), project, BIKE)
    restarted = production()
    assert ask(restarted, project, chat_model) == [source]
    assert any((tmp_path / "vectors").iterdir())


def test_s022_scoped_removal(chat_model) -> None:
    store = InMemoryVectorStore()
    container = build_container(vector_store=store, chat_model=chat_model)
    project = uuid4()
    bike = add(container, project, BIKE + "\n\nCheck the wheel rim.")
    bread = add(container, project, BREAD)
    assert len(store.store[bike]) == 2
    container.source.remove.execute(str(bike.value))
    record = container.assistant.indexed_document_repository.get_by_doc_ref_id(bike)
    assert record is not None and record.status is IndexStatus.PENDING
    assert not store.store.get(bike)
    assert ask(container, project, chat_model) == [bread]


def test_s023_offline_index_search_and_cleanup(production, chat_model) -> None:
    container = production()
    project = uuid4()
    source = add(container, project, BIKE)
    assert ask(container, project, chat_model) == [source]
    assistant = container.assistant
    probe = assistant.document_chunker.chunk(QUESTION)
    vector = assistant.embedding_generator.generate(probe)[0].vector
    container.source.remove.execute(str(source.value))
    assert assistant.vector_store.query(vector, doc_ref_ids=[source]) == []


@pytest.mark.parametrize("text", ["", " \t\n "])
def test_s024_blank_text(rag_container, text) -> None:
    assert rag_container.assistant.document_chunker.chunk(text) == []


def test_s025_test_startup_stays_in_memory(tmp_path) -> None:
    container = create_app({"TESTING": True}).extensions["container"]
    assistant = container.assistant
    assert isinstance(assistant.document_chunker, InMemoryDocumentChunker)
    assert isinstance(assistant.embedding_generator, InMemoryEmbeddingGenerator)
    assert isinstance(assistant.vector_store, InMemoryVectorStore)
    source = add(container, uuid4(), BIKE)
    [embedding] = assistant.vector_store.store[source]
    [hit] = assistant.vector_store.query(embedding.vector, doc_ref_ids=[source])
    assert hit.text == BIKE
    assert not (tmp_path / "vectors").exists()


def test_s026_remove_never_indexed(monkeypatch, caplog) -> None:
    bus = InProcessEventBus()
    container = build_container(publisher=bus)
    with monkeypatch.context() as patch:
        patch.setattr(bus, "publish", Mock())
        source = add(container, uuid4(), BIKE)
    assert container.assistant.indexed_document_repository.get_by_doc_ref_id(source) is None
    container.source.remove.execute(str(source.value))
    assert not [record for record in caplog.records if record.exc_info]


def test_s027_semantic_ranking(rag_container, chat_model, monkeypatch) -> None:
    container = rag_container
    generator = container.assistant.embedding_generator
    generate = Mock(wraps=generator.generate)
    monkeypatch.setattr(generator, "generate", generate)
    project = uuid4()
    bread = add(container, project, BREAD)
    bike = add(container, project, BIKE)
    assert ask(container, project, chat_model) == [bike, bread]
    bread_question = "How do I bake a loaf of bread?"
    assert ask(container, project, chat_model, bread_question) == [bread, bike]
    texts = [chunk.text for call in generate.call_args_list for chunk in call.args[0]]
    assert texts == [BREAD, BIKE, QUESTION, bread_question]


def test_s028_removal_during_indexing(monkeypatch) -> None:
    project = uuid4()
    store = InMemoryVectorStore()
    generator = InMemoryEmbeddingGenerator()
    container = build_container(vector_store=store, embedding_generator=generator)
    repo = container.assistant.indexed_document_repository
    paused, resume = Event(), Event()
    generate = generator.generate

    def pause(chunks: list[Chunk]) -> list:
        paused.set()
        assert resume.wait(10), "Indexing was never released"
        return generate(chunks)

    monkeypatch.setattr(generator, "generate", pause)
    with ThreadPoolExecutor(max_workers=1) as workers:
        job = workers.submit(add, container, project, BIKE)
        try:
            assert paused.wait(10), "Indexing did not reach embedding"
            [record] = repo.list_by_project(ProjectId(project))
            ref = record.doc_ref_id
            container.source.remove.execute(str(ref.value))
            during = repo.get_by_doc_ref_id(ref)
            assert during is not None
            status_at_removal = during.status
            vectors_at_removal = list(store.store.get(ref, []))
        finally:
            resume.set()
        assert job.result(timeout=10) == ref
    final = repo.get_by_doc_ref_id(ref)
    assert final is not None and final.status is IndexStatus.PENDING
    assert status_at_removal is IndexStatus.PENDING
    assert not vectors_at_removal and not store.store.get(ref)


def test_s022_cleanup_can_retry_after_vector_store_failure(monkeypatch) -> None:
    store = InMemoryVectorStore()
    container = build_container(vector_store=store)
    ref = add(container, uuid4(), BIKE)
    with monkeypatch.context() as patch:
        patch.setattr(store, "delete", Mock(side_effect=OSError("unavailable")))
        with pytest.raises(ExceptionGroup, match="Source removal cleanup failed"):
            container.source.remove.execute(str(ref.value))
    assert store.store[ref]
    container.source.remove.execute(str(ref.value))
    assert not store.store.get(ref)
