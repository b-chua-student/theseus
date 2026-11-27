import logging

from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.infrastructure.ports.document_parser import DocumentParser
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.value_objects import DocumentRefId, IndexStatus
from domain.assistant.services.indexing_state import IndexingState

logger = logging.getLogger(__name__)


class IngestionWorker:
    """Domain service that orchestrates the full ingestion pipeline for a single document.

    Coordinates the six infrastructure ports to fetch, parse, chunk, embed, and
    store a document's vector representations, keeping the IndexedDocument aggregate
    up to date throughout the process.
    """

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        source_provider: SourceContentProvider,
        parser: DocumentParser,
        chunker: DocumentChunker,
        embedding_generator: EmbeddingGenerator,
        vector_store: VectorStore,
        indexing_state: IndexingState | None = None,
    ) -> None:
        """Configure the dependencies for the document indexing pipeline."""
        self._repository = repository
        self._source_provider = source_provider
        self._parser = parser
        self._chunker = chunker
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._indexing_state = indexing_state or IndexingState()

    def process(self, doc_ref_id: DocumentRefId) -> None:
        """Run the ingestion pipeline for ``doc_ref_id`` and update its indexing status.

        Any step failure marks the document FAILED and is logged instead of raised.
        """
        state = self._indexing_state.for_document(doc_ref_id)
        job = object()
        with state.lock:
            doc = self._repository.get_by_doc_ref_id(doc_ref_id)
            if doc is None:
                logger.warning("No document to index for %s", doc_ref_id)
                return
            if doc.status is not IndexStatus.INDEXING:
                doc.start_indexing()
                self._repository.save(doc)
            state.active_job = job

        try:
            text = self._source_provider.get_content(doc_ref_id)
            chunks = self._chunker.chunk(self._parser.parse(text))
            if not chunks:
                raise ValueError("Chunker returned an empty list")
            embeddings = self._embedding_generator.generate(chunks)
            if len(embeddings) != len(chunks):
                raise ValueError(f"Expected {len(chunks)} embeddings, got {len(embeddings)}")
            with state.lock:
                if state.active_job is not job:
                    return
                self._vector_store.upsert(doc_ref_id, embeddings, chunks)
                doc.complete_indexing(chunks)
                self._repository.save(doc)
                state.active_job = None
        except Exception:
            with state.lock:
                if state.active_job is not job:
                    return
                if doc.status is IndexStatus.INDEXING:
                    doc.fail_indexing()
                    self._repository.save(doc)
                state.active_job = None
            logger.exception("Indexing failed for document %s", doc_ref_id)
