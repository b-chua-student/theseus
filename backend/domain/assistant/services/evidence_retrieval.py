from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace

from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.indexed_document_repository import (
    IndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.token_counter import TokenCounter
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.errors import InvalidDocumentRefIdError
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    ProjectId,
    RetrievedChunk,
    SourceOutcome,
    SourceStatus,
)

logger = logging.getLogger(__name__)

UNTITLED = "Untitled source"


@dataclass(frozen=True)
class Evidence:
    """The library evidence for one exchange.

    ``excerpts`` are the admitted passages. ``outcomes`` has a record for every selected source
    that supplied none. ``reported`` is the part of ``outcomes`` whose records fit in the
    request to the model; the rest are known only here.
    """

    excerpts: list[RetrievedChunk]
    outcomes: list[SourceOutcome]
    reported: list[SourceOutcome]

    def gap_report(self) -> str:
        """Return a named line for every source that supplied no evidence, if any is unreported.

        The model is told only the records that fit in its window. When some did not, this report
        names every source and the reason, so none is lost from the answer.
        """
        if len(self.reported) >= len(self.outcomes):
            return ""
        records = "\n".join(f"- {outcome.record()}" for outcome in self.outcomes)
        return f"**Selected sources not used as evidence**\n{records}"

    @classmethod
    def empty(cls) -> Evidence:
        """Return evidence with no passages and no outcomes."""
        return cls([], [], [])


@dataclass(frozen=True)
class _Candidate:
    chunk: RetrievedChunk
    tokens: int


@dataclass(frozen=True)
class _Search:
    ref: DocumentRefId
    title: str
    unavailable: bool
    candidates: list[_Candidate]


class EvidenceRetriever:
    """Finds passages in the selected library sources and fits them into the model's window.

    Every selected source of the project is searched on its own, so one source cannot use up
    another's share, and a failed search is isolated to its source. A passage is eligible when
    its cosine score is at or above ``relevance_threshold``. Eligible passages are admitted in
    rounds across sources, best source first, while they fit in the evidence budget: the
    context window, less the reserved response and the text that is always sent. A source whose
    passages all failed to fit is reported as omitted for capacity.
    """

    def __init__(  # noqa: PLR0913
        self,
        embedding_generator: EmbeddingGenerator | None,
        vector_store: VectorStore | None,
        document_repository: IndexedDocumentRepository | None,
        source_ids: Callable[[ProjectId], list[DocumentRefId]] | None,
        *,
        passages_per_source: int = 5,
        relevance_threshold: float | None = None,
        token_counter: TokenCounter | None = None,
        context_window: int | None = None,
        response_reserve: int = 0,
        batch_size: int = 50,
        workers: int = 8,
    ) -> None:
        """Configure retrieval. Without a counter and a window the evidence budget is unlimited."""
        self._embedding_generator = embedding_generator
        self._vector_store = vector_store
        self._document_repository = document_repository
        self._source_ids = source_ids
        self._passages_per_source = passages_per_source
        self._threshold = relevance_threshold
        self._counter = token_counter
        self._window = context_window
        self._reserve = response_reserve
        self._batch_size = max(1, batch_size)
        self._workers = max(1, workers)

    def retrieve(
        self,
        project_id: ProjectId,
        question: str,
        selected: Sequence[str] | None,
        *,
        quote: str | None = None,
        fixed_texts: Sequence[str] = (),
    ) -> Evidence:
        """Return the evidence for ``question`` from the selected sources of the project.

        ``selected`` are the requested source IDs; None means every active source of the
        project. IDs outside the project are ignored. ``fixed_texts`` are the history, question,
        draft and quote that are sent regardless, and are counted against the budget.
        """
        if (
            self._embedding_generator is None
            or self._vector_store is None
            or self._document_repository is None
            or self._source_ids is None
        ):
            return Evidence.empty()
        try:
            refs = self._selected_refs(project_id, selected)
            if not refs:
                return Evidence.empty()
            documents = {
                d.doc_ref_id: d for d in self._document_repository.list_by_project(project_id)
            }
            searches = self._search_all(refs, documents, question, quote)
            return self._admit(searches, self._budget(fixed_texts))
        except Exception:
            # Retrieval is best-effort: an outage shouldn't block chat.
            logger.exception("EvidenceRetriever: retrieval failed; answering without context")
            return Evidence.empty()

    def _selected_refs(
        self, project_id: ProjectId, selected: Sequence[str] | None
    ) -> list[DocumentRefId]:
        assert self._source_ids is not None
        allowed = self._source_ids(project_id)
        if selected is None:
            return list(dict.fromkeys(allowed))
        permitted = set(allowed)
        refs: dict[DocumentRefId, None] = {}
        for value in selected:
            try:
                ref = DocumentRefId.from_str(value)
            except InvalidDocumentRefIdError:
                continue
            if ref in permitted:
                refs[ref] = None
        return list(refs)

    def _search_all(
        self,
        refs: list[DocumentRefId],
        documents: dict[DocumentRefId, IndexedDocument],
        question: str,
        quote: str | None,
    ) -> list[_Search]:
        assert self._embedding_generator is not None
        text = f"{quote}\n{question}" if quote else question
        probe = Chunk(id=ChunkId.new(), text=text, position="", location="", content_hash="")
        try:
            [embedding] = self._embedding_generator.generate([probe])
        except Exception:
            logger.exception("EvidenceRetriever: embedding the question failed")
            return [
                _Search(ref, self._title(documents.get(ref)), unavailable=True, candidates=[])
                for ref in refs
            ]
        vector = embedding.vector

        def search(ref: DocumentRefId) -> _Search:
            return self._search(ref, documents.get(ref), vector)

        searches: list[_Search] = []
        with ThreadPoolExecutor(max_workers=min(self._workers, len(refs))) as pool:
            for start in range(0, len(refs), self._batch_size):
                searches.extend(pool.map(search, refs[start : start + self._batch_size]))
        return searches

    def _search(
        self, ref: DocumentRefId, document: IndexedDocument | None, vector: list[float]
    ) -> _Search:
        assert self._vector_store is not None
        title = self._title(document)
        if document is None or not document.is_searchable:
            return _Search(ref, title, unavailable=True, candidates=[])
        try:
            found = self._vector_store.query(vector, k=self._passages_per_source, doc_ref_ids=[ref])
            eligible = sorted(
                (
                    chunk
                    for chunk in found
                    if chunk.doc_ref_id == ref
                    and (self._threshold is None or chunk.score >= self._threshold)
                ),
                key=lambda chunk: chunk.score,
                reverse=True,
            )
            candidates = []
            for chunk in eligible:
                titled = replace(chunk, title=title)
                candidates.append(_Candidate(titled, self._excerpt_tokens(titled)))
        except Exception:
            logger.exception("EvidenceRetriever: searching source %s failed", ref.value)
            return _Search(ref, title, unavailable=True, candidates=[])
        return _Search(ref, title, unavailable=False, candidates=candidates)

    @staticmethod
    def _title(document: IndexedDocument | None) -> str:
        return document.title.value if document is not None else UNTITLED

    def _excerpt_tokens(self, chunk: RetrievedChunk) -> int:
        if self._counter is None:
            return 0
        return self._counter.count(f"{chunk.title} {chunk.location} {chunk.text}")

    def _budget(self, fixed_texts: Sequence[str]) -> int | None:
        """Return the tokens left for evidence, or None when the budget is unlimited."""
        if self._counter is None or self._window is None:
            return None
        fixed = sum(self._counter.count(text) for text in fixed_texts)
        return self._window - self._reserve - fixed

    def _admit(self, searches: list[_Search], budget: int | None) -> Evidence:
        queues = {
            s.ref: deque(s.candidates) for s in sorted(searches, key=self._best, reverse=True)
        }
        remaining = budget
        admitted: dict[DocumentRefId, list[RetrievedChunk]] = {s.ref: [] for s in searches}
        progress = True
        while progress:
            progress = False
            for ref, queue in queues.items():
                # Try smaller passages of this source before giving up on it.
                for candidate in queue:
                    if remaining is None or candidate.tokens <= remaining:
                        queue.remove(candidate)
                        admitted[ref].append(candidate.chunk)
                        if remaining is not None:
                            remaining -= candidate.tokens
                        progress = True
                        break

        outcomes: list[SourceOutcome] = []
        for search in searches:
            status = self._status(search, admitted[search.ref])
            if status is not None:
                outcomes.append(SourceOutcome(search.ref, search.title, status))
        excerpts = [chunk for ref in queues for chunk in admitted[ref]]
        return Evidence(excerpts, outcomes, self._fitting(outcomes, remaining))

    @staticmethod
    def _best(search: _Search) -> float:
        return max((c.chunk.score for c in search.candidates), default=float("-inf"))

    @staticmethod
    def _status(search: _Search, admitted: list[RetrievedChunk]) -> SourceStatus | None:
        if search.unavailable:
            return SourceStatus.UNAVAILABLE
        if admitted:
            return None
        if search.candidates:
            return SourceStatus.OMITTED_FOR_CAPACITY
        return SourceStatus.SEARCHED_WITHOUT_MATCH

    def _fitting(self, outcomes: list[SourceOutcome], remaining: int | None) -> list[SourceOutcome]:
        """Keep the whole outcome records that fit in what the budget has left."""
        if remaining is None or self._counter is None:
            return list(outcomes)
        fitting: list[SourceOutcome] = []
        for outcome in outcomes:
            cost = self._counter.count(outcome.record())
            if cost <= remaining:
                fitting.append(outcome)
                remaining -= cost
        return fitting
