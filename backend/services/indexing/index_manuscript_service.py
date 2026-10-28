from uuid import UUID

from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import IndexStatus
from services.indexing.create_indexed_document import CreateIndexedDocumentService
from services.indexing.embed_indexed_document import EmbedIndexedDocumentService
from services.indexing.save_indexed_document import SaveIndexedDocumentService
from services.manuscript.chunk_manuscript import ChunkManuscriptService
from services.manuscript.get_manuscript import GetManuscriptService


class IndexManuscriptService:
    """Application service that indexes a manuscript end to end.

    Pipeline: load, chunk, build the indexed document, embed, save.
    This service owns the status transitions and failure handling.
    """

    def __init__(
        self,
        get_manuscript: GetManuscriptService,
        chunk_manuscript: ChunkManuscriptService,
        create_indexed_document: CreateIndexedDocumentService,
        embed_indexed_document: EmbedIndexedDocumentService,
        save_indexed_document: SaveIndexedDocumentService,
    ) -> None:
        """Initialize the service.

        Args:
            get_manuscript: Loads the manuscript.
            chunk_manuscript: Splits section bodies into chunks.
            create_indexed_document: Builds the pending aggregate.
            embed_indexed_document: Generates chunk vectors.
            save_indexed_document: Persists the document and vectors.
        """
        self._get_manuscript = get_manuscript
        self._chunk_manuscript = chunk_manuscript
        self._create_indexed_document = create_indexed_document
        self._embed_indexed_document = embed_indexed_document
        self._save_indexed_document = save_indexed_document

    def execute(self, manuscript_id: UUID) -> IndexedDocument:
        """Index a manuscript.

        Args:
            manuscript_id: Id of the manuscript to index.

        Returns:
            The indexed document with status READY.

        Raises:
            Exception: Any embedding error is re-raised after the document
                is marked FAILED and saved. Load and chunk errors propagate
                before any document exists, so nothing is saved.
        """
        manuscript = self._get_manuscript.execute(manuscript_id)
        chunked = self._chunk_manuscript.execute(manuscript)
        indexed = self._create_indexed_document.execute(chunked)

        try:
            embeddings = self._embed_indexed_document.execute(indexed)
        except Exception:
            indexed.update_status(IndexStatus.FAILED)
            self._save_indexed_document.execute(indexed)
            raise

        indexed.update_status(IndexStatus.READY)
        self._save_indexed_document.execute(indexed, embeddings)
        return indexed
