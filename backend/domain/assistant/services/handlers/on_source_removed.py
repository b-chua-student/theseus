from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.value_objects import DocumentRefId
from domain.assistant.services.indexing_state import IndexingState
from domain.src_lib.models.events import SourceRemoved


class OnSourceRemoved:
    """Invalidate active indexing and clean up the removed document's vectors."""

    def __init__(
        self,
        repository: IndexedDocumentRepository,
        vector_store: VectorStore | None = None,
        indexing_state: IndexingState | None = None,
    ) -> None:
        """Use the same commit guard as the ingestion worker."""
        self._repository = repository
        self._vector_store = vector_store
        self._indexing_state = indexing_state or IndexingState()

    def __call__(self, event: SourceRemoved) -> None:
        """Mark a known source stale and delete its vectors, including on retry."""
        ref = DocumentRefId(event.source_id.value)
        state = self._indexing_state.for_document(ref)
        with state.lock:
            state.active_job = None
            doc = self._repository.get_by_doc_ref_id(ref)
            if doc is None:
                return
            doc.mark_stale()
            self._repository.save(doc)
            if self._vector_store is not None:
                self._vector_store.delete(ref)
