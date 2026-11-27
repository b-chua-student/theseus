"""Unit tests for re-embedding indexed documents after an embedding model change."""

from uuid import uuid4

from bootstrap.app import create_app
from bootstrap.container import build_container
from domain.assistant.infrastructure.adapters.in_memory_document_chunker import (
    InMemoryDocumentChunker,
)
from domain.assistant.infrastructure.adapters.in_memory_document_parser import (
    InMemoryDocumentParser,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import InMemoryVectorStore
from domain.assistant.infrastructure.adapters.in_process_index_job_queue import (
    InProcessIndexJobQueue,
)
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.models.aggregates import IndexedDocument
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
from domain.assistant.services.reindex_documents import ReindexDocumentsService


class VersionedEmbeddings(EmbeddingGenerator):
    """Embeds every chunk as ``[version]`` so a model change is visible in the vectors."""

    def __init__(self) -> None:
        self.version = 1.0

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        return [Embedding(chunk_id=chunk.id, vector=[self.version]) for chunk in chunks]


class StaticContent(SourceContentProvider):
    def get_content(self, doc_ref_id: DocumentRefId) -> str:
        return "Paragraph one.\n\nParagraph two."

    def get_title(self, doc_ref_id: DocumentRefId) -> str | None:
        return "Source"


def document(status: IndexStatus) -> IndexedDocument:
    doc = IndexedDocument.create(
        IndexedDocumentTitle("Source"), DocumentRefId.new(), ProjectId(uuid4())
    )
    if status is not IndexStatus.PENDING:
        doc.start_indexing()
    if status is IndexStatus.INDEXED:
        doc.complete_indexing(
            [Chunk(id=ChunkId.new(), text="t", position="1", location="p1", content_hash="t")]
        )
    elif status is IndexStatus.FAILED:
        doc.fail_indexing()
    return doc


def test_marks_indexed_documents_stale_and_requeues_all_but_indexing() -> None:
    repository = InMemoryIndexedDocumentRepository()
    queue = InProcessIndexJobQueue()
    docs = {status: document(status) for status in IndexStatus}
    for doc in docs.values():
        repository.add(doc)

    queued = ReindexDocumentsService(repository, queue).execute()

    assert queued == 3
    assert set(queue.pending) == {
        docs[status].doc_ref_id
        for status in (IndexStatus.PENDING, IndexStatus.INDEXED, IndexStatus.FAILED)
    }
    reindexed = repository.get_by_doc_ref_id(docs[IndexStatus.INDEXED].doc_ref_id)
    assert reindexed is not None
    assert reindexed.status is IndexStatus.PENDING


def test_reindexing_replaces_vectors_from_the_previous_model() -> None:
    repository = InMemoryIndexedDocumentRepository()
    queue = InProcessIndexJobQueue()
    vectors = InMemoryVectorStore()
    embeddings = VersionedEmbeddings()
    worker = IngestionWorker(
        repository=repository,
        source_provider=StaticContent(),
        parser=InMemoryDocumentParser(),
        chunker=InMemoryDocumentChunker(),
        embedding_generator=embeddings,
        vector_store=vectors,
    )
    queue.set_worker(worker.process)
    doc = document(IndexStatus.PENDING)
    repository.add(doc)
    queue.enqueue_index(doc.doc_ref_id)
    assert {e.vector[0] for e in vectors.store[doc.doc_ref_id]} == {1.0}

    embeddings.version = 2.0
    ReindexDocumentsService(repository, queue).execute()

    assert {e.vector[0] for e in vectors.store[doc.doc_ref_id]} == {2.0}
    stored = repository.get_by_doc_ref_id(doc.doc_ref_id)
    assert stored is not None
    assert stored.status is IndexStatus.INDEXED


def test_cli_command_reports_the_number_of_requeued_documents() -> None:
    container = build_container()
    assert container.assistant.reindex is not None
    app = create_app({"TESTING": True}, container=container)

    result = app.test_cli_runner().invoke(args=["reindex-documents"])

    assert result.exit_code == 0
    assert "Re-queued 0 documents" in result.output
