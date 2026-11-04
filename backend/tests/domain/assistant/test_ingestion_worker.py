"""Tests for IngestionWorker — tasks 4.1 through 4.9.

Covers:
  Requirements 1.1–1.5, 2.1–2.2, 3.1–3.2, 4.1–4.3, 5.1–5.3,
  6.1–6.2, 7.1–7.3, 8.1–8.4, 9.1–9.6, 10.1–10.2
"""

from __future__ import annotations

from unittest.mock import patch

from hypothesis import given, settings
from hypothesis import strategies as st

from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.infrastructure.ports.document_parser import DocumentParser
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.errors import InvalidIndexTransitionError
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    Embedding,
    IndexedDocumentTitle,
    IndexStatus,
    ProjectId,
)
from domain.assistant.services.ingestion_worker import IngestionWorker

# ---------------------------------------------------------------------------
# Task 4.1 — Stub port implementations
# ---------------------------------------------------------------------------


class StubSourceContentProvider(SourceContentProvider):
    def __init__(self, content: str = "hello world", raises: Exception | None = None) -> None:
        self.content = content
        self.raises = raises

    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        if self.raises:
            raise self.raises
        return self.content


class StubDocumentParser(DocumentParser):
    def __init__(self, result: str = "parsed text", raises: Exception | None = None) -> None:
        self.result = result
        self.raises = raises

    def parse(self, raw_text: str) -> str:
        if self.raises:
            raise self.raises
        return self.result


class StubDocumentChunker(DocumentChunker):
    def __init__(
        self,
        chunks: list[Chunk] | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._chunks = chunks  # None means auto-generate one chunk
        self.raises = raises

    def chunk(self, structured_text: str) -> list[Chunk]:
        if self.raises:
            raise self.raises
        if self._chunks is not None:
            return self._chunks
        return [
            Chunk(
                id=ChunkId.new(),
                text=structured_text[:50],
                position="0",
                location="p1",
                content_hash="abc",
            )
        ]


class StubEmbeddingGenerator(EmbeddingGenerator):
    def __init__(self, raises: Exception | None = None, wrong_count: bool = False) -> None:
        self.raises = raises
        self.wrong_count = wrong_count

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        if self.raises:
            raise self.raises
        result = [Embedding(chunk_id=c.id, vector=[0.1, 0.2]) for c in chunks]
        if self.wrong_count:
            return result[:-1]  # drop one to cause mismatch
        return result


class StubVectorStore(VectorStore):
    def __init__(self, raises: Exception | None = None) -> None:
        self.raises = raises
        self.upserted: dict = {}

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        if self.raises:
            raise self.raises
        self.upserted[doc_ref_id] = embeddings

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        self.upserted.pop(doc_ref_id, None)

    def query(self, query_embedding, k=5, doc_ref_ids=None):  # type: ignore[no-untyped-def]
        return []


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_worker(
    repo: InMemoryIndexedDocumentRepository | None = None,
    provider: SourceContentProvider | None = None,
    parser: DocumentParser | None = None,
    chunker: DocumentChunker | None = None,
    embedding_generator: EmbeddingGenerator | None = None,
    vector_store: VectorStore | None = None,
) -> IngestionWorker:
    """Build a fully-wired IngestionWorker, using stubs for any unspecified ports."""
    return IngestionWorker(
        repository=repo or InMemoryIndexedDocumentRepository(),
        source_provider=provider or StubSourceContentProvider(),
        parser=parser or StubDocumentParser(),
        chunker=chunker or StubDocumentChunker(),
        embedding_generator=embedding_generator or StubEmbeddingGenerator(),
        vector_store=vector_store or StubVectorStore(),
    )


def make_document(
    status: IndexStatus = IndexStatus.PENDING,
) -> tuple[IngestionWorker, InMemoryIndexedDocumentRepository, IndexedDocument]:
    """Create a document, persist it in a fresh repo, return (worker, repo, doc)."""
    repo = InMemoryIndexedDocumentRepository()
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Test Document"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    # Force the desired status without going through the state machine for non-PENDING
    if status != IndexStatus.PENDING:
        doc.start_indexing()  # PENDING → INDEXING
        if status == IndexStatus.INDEXED:
            # need at least one chunk to complete
            doc.complete_indexing(
                [
                    Chunk(
                        id=ChunkId.new(), text="seed", position="0", location="p0", content_hash="x"
                    )
                ]
            )
        elif status == IndexStatus.FAILED:
            doc.fail_indexing()
        # INDEXING is reached above already
    repo.add(doc)
    worker = make_worker(repo=repo)
    return worker, repo, doc


# ---------------------------------------------------------------------------
# Tasks 4.2–4.4 — Example-based tests
# ---------------------------------------------------------------------------


def test_happy_path() -> None:
    """All stubs succeed; document ends up INDEXED with correct chunks."""
    repo = InMemoryIndexedDocumentRepository()
    chunker = StubDocumentChunker()
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)

    worker = make_worker(repo=repo, chunker=chunker)
    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.INDEXED
    # Chunks stored on the document should equal what the chunker produced
    expected_chunks = chunker.chunk("parsed text")
    assert len(saved.chunks) == len(expected_chunks)


def test_document_not_found() -> None:
    """Worker exits silently when the document is not in the repository."""
    repo = InMemoryIndexedDocumentRepository()
    unknown_ref = DocumentRefId.new()
    worker = make_worker(repo=repo)

    # Should not raise
    worker.process(unknown_ref)

    # Repo remains empty
    assert repo.get_by_doc_ref_id(unknown_ref) is None


def test_content_retrieval_failure() -> None:
    """Provider raises → document ends up FAILED."""
    _, repo, doc = make_document()
    provider = StubSourceContentProvider(raises=RuntimeError("network error"))
    worker = make_worker(repo=repo, provider=provider)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_parser_failure() -> None:
    """Parser raises → document ends up FAILED."""
    _, repo, doc = make_document()
    parser = StubDocumentParser(raises=ValueError("bad format"))
    worker = make_worker(repo=repo, parser=parser)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_chunker_raises() -> None:
    """Chunker raises → document ends up FAILED."""
    _, repo, doc = make_document()
    chunker = StubDocumentChunker(raises=RuntimeError("chunking exploded"))
    worker = make_worker(repo=repo, chunker=chunker)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_chunker_returns_empty_list() -> None:
    """Chunker returns [] → document ends up FAILED."""
    _, repo, doc = make_document()
    chunker = StubDocumentChunker(chunks=[])
    worker = make_worker(repo=repo, chunker=chunker)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_embedding_generator_raises() -> None:
    """Embedding generator raises → document ends up FAILED."""
    _, repo, doc = make_document()
    gen = StubEmbeddingGenerator(raises=RuntimeError("GPU OOM"))
    worker = make_worker(repo=repo, embedding_generator=gen)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_embedding_count_mismatch() -> None:
    """Generator returns fewer embeddings than chunks → document ends up FAILED."""
    # Need at least 2 chunks for wrong_count to take effect (drops one)
    repo = InMemoryIndexedDocumentRepository()
    chunks = [
        Chunk(
            id=ChunkId.new(), text=f"chunk {i}", position=str(i), location="p1", content_hash=str(i)
        )
        for i in range(2)
    ]
    chunker = StubDocumentChunker(chunks=chunks)
    gen = StubEmbeddingGenerator(wrong_count=True)
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)
    worker = make_worker(repo=repo, chunker=chunker, embedding_generator=gen)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_vector_store_upsert_raises() -> None:
    """Vector store upsert raises → document ends up FAILED."""
    _, repo, doc = make_document()
    store = StubVectorStore(raises=OSError("disk full"))
    worker = make_worker(repo=repo, vector_store=store)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


def test_document_already_indexing() -> None:
    """Document already in INDEXING state; worker skips start_indexing and completes normally."""
    repo = InMemoryIndexedDocumentRepository()
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    doc.start_indexing()  # manually advance to INDEXING
    repo.add(doc)

    worker = make_worker(repo=repo)
    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.INDEXED


def test_fail_indexing_invalid_transition() -> None:
    """fail_indexing absorbs InvalidIndexTransitionError and returns normally."""
    _, repo, doc = make_document()
    # Make content retrieval fail to trigger _handle_failure path
    provider = StubSourceContentProvider(raises=RuntimeError("boom"))
    worker = make_worker(repo=repo, provider=provider)

    # Patch the doc's fail_indexing to raise InvalidIndexTransitionError after start_indexing
    original_get = repo.get_by_doc_ref_id

    def patched_get(doc_ref_id: DocumentRefId) -> IndexedDocument | None:
        found = original_get(doc_ref_id)
        if found is not None:
            # Wrap fail_indexing on the live object
            found.fail_indexing = lambda: (_ for _ in ()).throw(  # type: ignore[method-assign]
                InvalidIndexTransitionError(IndexStatus.INDEXING, IndexStatus.FAILED)
            )
        return found

    with patch.object(repo, "get_by_doc_ref_id", side_effect=patched_get):
        # Must not propagate the error
        worker.process(doc.doc_ref_id)


# ---------------------------------------------------------------------------
# Tasks 4.5–4.9 — Property-based tests (Hypothesis)
# ---------------------------------------------------------------------------

# Shared Hypothesis strategy for generating valid Chunk objects
chunk_strategy = st.builds(
    Chunk,
    id=st.builds(ChunkId, value=st.uuids()),
    text=st.text(min_size=1, max_size=200),
    position=st.text(max_size=50),
    location=st.text(max_size=50),
    content_hash=st.text(max_size=64),
)


# Feature: ingestion-worker, Property 5: Missing document stops processing without exception
# Validates: Requirements 5.1
@settings(max_examples=100)
@given(doc_ref_id=st.builds(DocumentRefId, value=st.uuids()))
def test_property_5_missing_document_no_exception(doc_ref_id: DocumentRefId) -> None:
    """For any DocumentRefId not in the repo, process() never raises."""
    repo = InMemoryIndexedDocumentRepository()
    worker = make_worker(repo=repo)

    # Must not raise for any ref id
    worker.process(doc_ref_id)

    # Nothing was written either
    assert repo.get_by_doc_ref_id(doc_ref_id) is None


# Feature: ingestion-worker, Property 1: Full-pipeline chunk round-trip
# Validates: Requirements 1.1–1.5
@settings(max_examples=100)
@given(chunks=st.lists(chunk_strategy, min_size=1))
def test_property_1_chunk_round_trip(chunks: list[Chunk]) -> None:
    """Chunks produced by the chunker are exactly what is stored on the document."""
    repo = InMemoryIndexedDocumentRepository()
    chunker = StubDocumentChunker(chunks=chunks)
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)
    worker = make_worker(repo=repo, chunker=chunker)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.INDEXED
    assert saved.chunks == chunks


# Feature: ingestion-worker, Property 4: Successful pipeline ends in INDEXED state
# Validates: Requirements 4.1–4.3
@settings(max_examples=100)
@given(chunks=st.lists(chunk_strategy, min_size=1))
def test_property_4_success_ends_indexed(chunks: list[Chunk]) -> None:
    """Any non-empty chunk list causes the document to reach INDEXED."""
    repo = InMemoryIndexedDocumentRepository()
    chunker = StubDocumentChunker(chunks=chunks)
    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)
    worker = make_worker(repo=repo, chunker=chunker)

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.INDEXED


# Feature: ingestion-worker, Property 2: Failure leaves document in FAILED state
# Validates: Requirements 2.1–2.2
@settings(max_examples=100)
@given(failing_step=st.sampled_from(["content", "parse", "chunk", "embed", "upsert"]))
def test_property_2_failure_leaves_failed(failing_step: str) -> None:
    """Whichever pipeline step raises, the document must end up FAILED."""
    repo = InMemoryIndexedDocumentRepository()
    error = RuntimeError(f"{failing_step} exploded")

    provider = StubSourceContentProvider(raises=error if failing_step == "content" else None)
    parser = StubDocumentParser(raises=error if failing_step == "parse" else None)
    chunker = StubDocumentChunker(raises=error if failing_step == "chunk" else None)
    gen = StubEmbeddingGenerator(raises=error if failing_step == "embed" else None)
    store = StubVectorStore(raises=error if failing_step == "upsert" else None)

    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)
    worker = make_worker(
        repo=repo,
        provider=provider,
        parser=parser,
        chunker=chunker,
        embedding_generator=gen,
        vector_store=store,
    )

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED


# Feature: ingestion-worker, Property 3: Embedding count invariant
# Validates: Requirements 3.1–3.2
@settings(max_examples=100)
@given(
    chunks=st.lists(chunk_strategy, min_size=2),
    drop=st.integers(min_value=1),
)
def test_property_3_embedding_count_invariant(chunks: list[Chunk], drop: int) -> None:
    """When embedding count ≠ chunk count, the document must end up FAILED."""
    # Clip drop so we always return at least zero embeddings but fewer than len(chunks)
    actual_drop = (drop - 1) % len(chunks) + 1  # 1 .. len(chunks)

    repo = InMemoryIndexedDocumentRepository()
    chunker = StubDocumentChunker(chunks=chunks)

    class CountMismatchGenerator(EmbeddingGenerator):
        def generate(self, cks: list[Chunk]) -> list[Embedding]:
            full = [Embedding(chunk_id=c.id, vector=[0.1, 0.2]) for c in cks]
            return full[: len(full) - actual_drop]  # always fewer than len(chunks)

    doc = IndexedDocument.create(
        title=IndexedDocumentTitle("Doc"),
        doc_ref_id=DocumentRefId.new(),
        project_id=ProjectId.new(),
    )
    repo.add(doc)
    worker = make_worker(
        repo=repo,
        chunker=chunker,
        embedding_generator=CountMismatchGenerator(),
    )

    worker.process(doc.doc_ref_id)

    saved = repo.get_by_doc_ref_id(doc.doc_ref_id)
    assert saved is not None
    assert saved.status == IndexStatus.FAILED
