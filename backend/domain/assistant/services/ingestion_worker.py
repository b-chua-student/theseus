import logging

from domain.assistant.infrastructure.ports.document_chunker import DocumentChunker
from domain.assistant.infrastructure.ports.document_parser import DocumentParser
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.source_content_provider import SourceContentProvider
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.errors import InvalidIndexTransitionError
from domain.assistant.models.value_objects import DocumentRefId, IndexStatus

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
    ) -> None:
        self._repository = repository
        self._source_provider = source_provider
        self._parser = parser
        self._chunker = chunker
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store

    def process(self, doc_ref_id: DocumentRefId) -> None:
        """Run the ingestion pipeline for ``doc_ref_id`` and update its indexing status.

        Any step failure marks the document FAILED and is logged instead of raised.
        """
        # Step 1 & 2: Lookup and state transition
        doc = self._repository.get_by_doc_ref_id(doc_ref_id)
        if doc is None:
            logger.warning("IngestionWorker: document not found doc_ref_id=%s", doc_ref_id)
            return

        if doc.status is not IndexStatus.INDEXING:
            doc.start_indexing()
            self._repository.save(doc)

        # Step 3: Fetch raw content
        try:
            raw_text = self._source_provider.get_content(doc_ref_id)
        except Exception as exc:
            self._handle_failure(doc, exc, "content retrieval", doc_ref_id)
            return

        # Step 4: Parse
        try:
            structured_text = self._parser.parse(raw_text)
        except Exception as exc:
            self._handle_failure(doc, exc, "parsing", doc_ref_id)
            return

        # Step 5: Chunk
        try:
            chunks = self._chunker.chunk(structured_text)
            if not chunks:
                raise ValueError("Chunker returned an empty list")
        except Exception as exc:
            self._handle_failure(doc, exc, "chunking", doc_ref_id)
            return

        # Step 6: Generate embeddings
        try:
            embeddings = self._embedding_generator.generate(chunks)
            if len(embeddings) != len(chunks):
                raise ValueError(
                    f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}"
                )
        except Exception as exc:
            self._handle_failure(doc, exc, "embedding generation", doc_ref_id)
            return

        # Step 7: Upsert into vector store
        try:
            self._vector_store.upsert(doc_ref_id, embeddings, chunks)
        except Exception as exc:
            self._handle_failure(doc, exc, "vector upsert", doc_ref_id)
            return

        # Step 8: Success path
        doc.complete_indexing(chunks)
        self._repository.save(doc)
        logger.info(
            "IngestionWorker: indexing complete doc_ref_id=%s chunks=%d",
            doc_ref_id,
            len(chunks),
        )

    def _handle_failure(
        self,
        doc: IndexedDocument,
        exc: Exception,
        step_name: str,
        doc_ref_id: DocumentRefId,
    ) -> None:
        try:
            doc.fail_indexing()
        except InvalidIndexTransitionError:
            logger.warning(
                "IngestionWorker: state-machine conflict in fail_indexing doc_ref_id=%s",
                doc_ref_id,
            )
            return

        self._repository.save(doc)
        logger.exception(
            "IngestionWorker: %s failed doc_ref_id=%s",
            step_name,
            doc_ref_id,
            exc_info=exc,
        )
