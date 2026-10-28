from chromadb.api.models.Collection import Collection

from domain.indexing.aggregates import IndexedDocument
from domain.indexing.value_objects import Embedding
from repositories.indexing.indexed_document_repository import (
    IndexedDocumentRepository,
)


class ChromaIndexedDocumentRepository(IndexedDocumentRepository):
    """ChromaDB-backed repository for indexed documents.

    Each chunk is stored as one Chroma record. Document-level fields are
    denormalized into every chunk's metadata. Vectors are supplied by the
    caller, so Chroma never embeds text itself.
    """

    def __init__(self, collection: Collection) -> None:
        """Initialize the repository.

        Args:
            collection: Chroma collection that stores chunk records. It
                must not rely on its own embedding function.
        """
        self._collection = collection

    def save(
        self,
        indexed_document: IndexedDocument,
        embeddings: list[Embedding] | None = None,
    ) -> None:
        """Replace a document's stored chunks.

        Chunks are stored only when vectors are supplied. Without vectors
        (for example a FAILED document), existing chunks are removed and
        nothing new is written, so no wrong-model vectors are created.

        Args:
            indexed_document: The indexed document to persist.
            embeddings: One embedding per chunk, or None.

        Raises:
            ValueError: If the embeddings do not match the chunks.
        """
        document_id = str(indexed_document.indexed_document_id.value)

        self._collection.delete(where={"indexed_document_id": document_id})

        chunks = indexed_document.chunks
        if not chunks or not embeddings:
            return

        vectors_by_chunk = {e.chunk_id: e.value for e in embeddings}

        if set(vectors_by_chunk) != {chunk.id for chunk in chunks}:
            raise ValueError("Embeddings must match the document's chunks exactly")

        self._collection.upsert(
            ids=[str(chunk.id) for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=[vectors_by_chunk[chunk.id] for chunk in chunks],
            metadatas=[
                {
                    "indexed_document_id": document_id,
                    "owner_kind": indexed_document.owner_kind.value,
                    "owner_id": str(indexed_document.owner_id),
                    "content_hash": indexed_document.content_hash.value,
                    "status": indexed_document.status.value,
                    "model_name": indexed_document.model.name,
                    "model_version": indexed_document.model.version,
                    "ordinal": chunk.ordinal,
                    "section_id": str(chunk.location.section_id),
                    "start_index": chunk.location.start_index,
                    "end_index": chunk.location.end_index,
                }
                for chunk in chunks
            ],
        )
