import builtins
from collections.abc import Callable, Collection

from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.errors import RetrievalError
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    Evidence,
    ProjectId,
    Query,
    RetrievedChunk,
)


class EvidenceRetriever:
    """Finds passages in a project's searchable sources.

    Retrieval needs the embedding generator, vector store, document repository and an active
    source ID reader. Without all four, a search finds nothing. A search that fails raises
    ``RetrievalError``, which differs from a successful search that finds no passages.
    """

    def __init__(
        self,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_store: VectorStore | None = None,
        document_repository: IndexedDocumentRepository | None = None,
        source_ids: Callable[[ProjectId], builtins.list[DocumentRefId]] | None = None,
        top_k: int = 5,
    ) -> None:
        """Configure the retrieval ports and how many passages a search returns."""
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._document_repository = document_repository
        self._source_ids = source_ids
        self._top_k = top_k

    def search(
        self,
        project_id: ProjectId,
        text: str,
        source_ids: builtins.list[str] | None = None,
    ) -> builtins.list[RetrievedChunk]:
        """Return the top passages for ``text`` from the project's searchable sources.

        ``source_ids`` narrows the search to the sources the user selected.

        Raises:
            RetrievalError: If the lookup itself fails.
        """
        if (
            self._embedding_generator is None
            or self._vector_store is None
            or self._document_repository is None
            or self._source_ids is None
        ):
            return []
        try:
            allowed = set(self._source_ids(project_id))
            if source_ids is not None:
                selected = set(source_ids)
                allowed = {ref for ref in allowed if str(ref.value) in selected}
            doc_ref_ids = [
                d.doc_ref_id
                for d in self._document_repository.list_by_project(project_id)
                if d.is_searchable and d.doc_ref_id in allowed
            ]
            if not doc_ref_ids:
                return []
            # The generator embeds chunks, so wrap the text as a throwaway chunk.
            probe = Chunk(id=ChunkId.new(), text=text, position="", location="", content_hash="")
            [embedding] = self._embedding_generator.generate([probe])
            return self._vector_store.query(
                embedding.vector, k=self._top_k, doc_ref_ids=doc_ref_ids
            )
        except Exception as exc:
            raise RetrievalError("Searching the sources failed.") from exc

    def find_more(
        self,
        project_id: ProjectId,
        question: Query,
        evidence: Evidence,
        missing_evidence: str | None,
        source_ids: builtins.list[str] | None = None,
        keep: Collection[int] | None = None,
    ) -> Evidence:
        """Search again for the original question and merge what is found into ``evidence``.

        The search keeps the request's source scope. Passages already in ``evidence`` keep their
        keys, and the result never exceeds the evidence budget. ``keep`` lists the keys that the
        current draft cites. When the evidence is full, passages outside ``keep`` make room for
        new ones; without ``keep`` nothing is given up.

        Raises:
            RetrievalError: If the lookup itself fails.
        """
        text = f"{question.text}\n{missing_evidence}" if missing_evidence else question.text
        found = self.search(project_id, text, source_ids)
        return evidence.merge(found, self._top_k, keep)
