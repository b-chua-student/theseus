"""Unit tests for per-source evidence retrieval, threshold and budget (T-008)."""

from dataclasses import dataclass, field

import pytest

from domain.assistant.infrastructure.adapters.in_memory_embedding_generator import (
    InMemoryEmbeddingGenerator,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.token_counter import TokenCounter
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import (
    Chunk,
    ChunkId,
    DocumentRefId,
    Embedding,
    IndexedDocumentTitle,
    ProjectId,
    RetrievedChunk,
    SourceStatus,
)
from domain.assistant.services.evidence_retrieval import UNTITLED, EvidenceRetriever

THRESHOLD = 0.5


class ScriptedStore(VectorStore):
    """Vector store that returns scripted (text, score) passages per source."""

    def __init__(self) -> None:
        self.passages: dict[DocumentRefId, list[tuple[str, float]]] = {}
        self.broken: set[DocumentRefId] = set()
        self.searched: list[DocumentRefId] = []

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        raise NotImplementedError

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        raise NotImplementedError

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        assert doc_ref_ids is not None
        results = []
        for ref in doc_ref_ids:
            self.searched.append(ref)
            if ref in self.broken:
                raise RuntimeError("store down")
            for index, (text, score) in enumerate(self.passages.get(ref, []), 1):
                results.append(
                    RetrievedChunk(ChunkId.new(), ref, text, str(index), f"p{index}", score)
                )
        results.sort(key=lambda chunk: chunk.score, reverse=True)
        return results[:k]


@dataclass
class WordCounter(TokenCounter):
    """Counts each registered text at its cost and everything else at zero."""

    costs: dict[str, int] = field(default_factory=dict)

    def count(self, text: str) -> int:
        return sum(cost * text.count(snippet) for snippet, cost in self.costs.items())


class BrokenEmbedder(EmbeddingGenerator):
    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        raise RuntimeError("embedder down")


class Fixture:
    def __init__(self) -> None:
        self.project = ProjectId.new()
        self.store = ScriptedStore()
        self.documents = InMemoryIndexedDocumentRepository()
        self.active: list[DocumentRefId] = []
        self.counter = WordCounter()

    def source(
        self, title: str, *passages: tuple[str, float], indexed: bool = True
    ) -> DocumentRefId:
        ref = DocumentRefId.new()
        document = IndexedDocument.create(IndexedDocumentTitle(title), ref, self.project)
        if indexed:
            document.start_indexing()
            document.complete_indexing([Chunk(ChunkId.new(), title, "1", "p1", content_hash=title)])
        self.documents.add(document)
        self.store.passages[ref] = list(passages)
        self.active.append(ref)
        return ref

    def retriever(self, **options: object) -> EvidenceRetriever:
        return EvidenceRetriever(
            InMemoryEmbeddingGenerator(),
            self.store,
            self.documents,
            lambda _project: list(self.active),
            **options,  # type: ignore[arg-type]
        )


@pytest.fixture
def fx() -> Fixture:
    return Fixture()


def statuses(evidence) -> dict[str, SourceStatus]:  # noqa: ANN001
    return {outcome.title: outcome.status for outcome in evidence.outcomes}


def test_a_passage_at_the_threshold_is_admitted_and_one_below_is_not(fx: Fixture) -> None:
    fx.source("At", ("at the line", THRESHOLD))
    fx.source("Below", ("just under", THRESHOLD - 0.001))

    evidence = fx.retriever(relevance_threshold=THRESHOLD).retrieve(fx.project, "q", None)

    assert [chunk.title for chunk in evidence.excerpts] == ["At"]
    assert statuses(evidence) == {"Below": SourceStatus.SEARCHED_WITHOUT_MATCH}


def test_a_source_with_no_passages_is_searched_without_a_match(fx: Fixture) -> None:
    fx.source("Empty")

    evidence = fx.retriever().retrieve(fx.project, "q", None)

    assert statuses(evidence) == {"Empty": SourceStatus.SEARCHED_WITHOUT_MATCH}


def test_a_failed_search_makes_only_that_source_unavailable(fx: Fixture) -> None:
    broken = fx.source("Broken", ("never seen", 0.9))
    fx.source("Fine", ("seen", 0.9))
    fx.store.broken.add(broken)

    evidence = fx.retriever().retrieve(fx.project, "q", None)

    assert [chunk.title for chunk in evidence.excerpts] == ["Fine"]
    assert statuses(evidence) == {"Broken": SourceStatus.UNAVAILABLE}


def test_a_source_that_is_not_indexed_is_unavailable_and_not_searched(fx: Fixture) -> None:
    pending = fx.source("Pending", ("hidden", 0.9), indexed=False)

    evidence = fx.retriever().retrieve(fx.project, "q", None)

    assert statuses(evidence) == {"Pending": SourceStatus.UNAVAILABLE}
    assert pending not in fx.store.searched


def test_a_source_without_a_document_is_unavailable_and_untitled(fx: Fixture) -> None:
    fx.active.append(DocumentRefId.new())

    evidence = fx.retriever().retrieve(fx.project, "q", None)

    assert statuses(evidence) == {UNTITLED: SourceStatus.UNAVAILABLE}


def test_a_failed_question_embedding_makes_every_selected_source_unavailable(fx: Fixture) -> None:
    fx.source("One", ("a", 0.9))
    fx.source("Two", ("b", 0.9))
    retriever = EvidenceRetriever(
        BrokenEmbedder(), fx.store, fx.documents, lambda _project: list(fx.active)
    )

    evidence = retriever.retrieve(fx.project, "q", None)

    assert evidence.excerpts == []
    assert statuses(evidence) == {
        "One": SourceStatus.UNAVAILABLE,
        "Two": SourceStatus.UNAVAILABLE,
    }


def test_only_selected_sources_of_the_project_are_searched(fx: Fixture) -> None:
    chosen = fx.source("Chosen", ("yes", 0.9))
    fx.source("Unchosen", ("no", 0.99))
    foreign = DocumentRefId.new()
    fx.store.passages[foreign] = [("foreign", 0.99)]

    evidence = fx.retriever().retrieve(
        fx.project, "q", [str(chosen.value), str(foreign.value), "not-a-uuid"]
    )

    assert [chunk.title for chunk in evidence.excerpts] == ["Chosen"]
    assert fx.store.searched == [chosen]


def test_every_source_of_a_selection_above_1000_is_searched(fx: Fixture) -> None:
    refs = [fx.source(f"S{index}", ("hit", 0.9)) for index in range(1001)]

    evidence = fx.retriever(batch_size=100).retrieve(fx.project, "q", [str(r.value) for r in refs])

    assert set(fx.store.searched) == set(refs)
    assert len(evidence.excerpts) == 1001
    assert evidence.outcomes == []


def test_without_a_budget_each_source_gives_up_to_its_passage_limit(fx: Fixture) -> None:
    fx.source("Many", *[(f"m{i}", 0.9) for i in range(10)])

    evidence = fx.retriever(passages_per_source=3).retrieve(fx.project, "q", None)

    assert len(evidence.excerpts) == 3


def test_a_source_with_many_matches_does_not_crowd_out_another(fx: Fixture) -> None:
    fx.source("Many", *[(f"many {i}", 0.95) for i in range(5)])
    fx.source("One", ("one", 0.8))
    fx.counter.costs.update({f"many {i}": 30 for i in range(5)} | {"one": 30})

    evidence = fx.retriever(token_counter=fx.counter, context_window=70).retrieve(
        fx.project, "q", None
    )

    assert sorted(chunk.title for chunk in evidence.excerpts) == ["Many", "One"]
    assert evidence.outcomes == []


def test_a_smaller_passage_is_tried_before_a_source_is_omitted(fx: Fixture) -> None:
    fx.source("Mixed", ("big passage", 0.9), ("small passage", 0.8))
    fx.counter.costs.update({"big passage": 500, "small passage": 20})

    evidence = fx.retriever(token_counter=fx.counter, context_window=100).retrieve(
        fx.project, "q", None
    )

    assert [chunk.text for chunk in evidence.excerpts] == ["small passage"]
    assert evidence.outcomes == []


def test_a_matching_source_none_of_whose_passages_fit_is_omitted_for_capacity(
    fx: Fixture,
) -> None:
    fx.source("Fits", ("fits", 0.9))
    fx.source("Huge", ("huge", 0.8))
    fx.counter.costs.update({"fits": 40, "huge": 150})

    evidence = fx.retriever(token_counter=fx.counter, context_window=100).retrieve(
        fx.project, "q", None
    )

    assert [chunk.title for chunk in evidence.excerpts] == ["Fits"]
    assert statuses(evidence) == {"Huge": SourceStatus.OMITTED_FOR_CAPACITY}


def test_the_budget_is_the_window_less_the_reserve_and_the_fixed_text(fx: Fixture) -> None:
    fx.source("Passage", ("passage", 0.9))
    fx.counter.costs.update({"passage": 40, "draft": 50})
    retriever = fx.retriever(token_counter=fx.counter, context_window=100, response_reserve=20)

    roomy = retriever.retrieve(fx.project, "q", None, fixed_texts=["short"])
    tight = retriever.retrieve(fx.project, "q", None, fixed_texts=["draft"])

    assert len(roomy.excerpts) == 1  # 100 - 20 - 0 = 80 fits 40
    assert tight.excerpts == []  # 100 - 20 - 50 = 30 does not fit 40
    assert statuses(tight) == {"Passage": SourceStatus.OMITTED_FOR_CAPACITY}


def test_only_whole_outcome_records_that_fit_are_reported(fx: Fixture) -> None:
    fx.source("Delta", ("delta", 0.9))
    for title in ("Alpha", "Beta", "Gamma"):
        fx.source(title, (f"{title} passage", 0.8))
        fx.counter.costs[f"{title} passage"] = 200
        fx.counter.costs[title] = 10
    fx.counter.costs["delta"] = 50
    retriever = fx.retriever(
        token_counter=fx.counter, context_window=50 + 10 + 5, response_reserve=5
    )

    evidence = retriever.retrieve(fx.project, "q", None)

    assert [chunk.title for chunk in evidence.excerpts] == ["Delta"]
    assert len(evidence.outcomes) == 3
    assert len(evidence.reported) == 1
    assert evidence.reported[0] in evidence.outcomes


def test_nothing_fits_when_the_fixed_text_alone_exceeds_the_window(fx: Fixture) -> None:
    fx.source("Passage", ("passage", 0.9))
    fx.counter.costs.update({"passage": 1, "draft": 500})

    evidence = fx.retriever(token_counter=fx.counter, context_window=100).retrieve(
        fx.project, "q", None, fixed_texts=["draft"]
    )

    assert evidence.excerpts == []
    assert evidence.reported == []
    assert statuses(evidence) == {"Passage": SourceStatus.OMITTED_FOR_CAPACITY}


def test_the_quote_is_embedded_with_the_question(fx: Fixture) -> None:
    fx.source("S", ("x", 0.9))
    embedded: list[str] = []

    class Recording(InMemoryEmbeddingGenerator):
        def generate(self, chunks: list[Chunk]) -> list[Embedding]:
            embedded.extend(chunk.text for chunk in chunks)
            return super().generate(chunks)

    retriever = EvidenceRetriever(
        Recording(), fx.store, fx.documents, lambda _project: list(fx.active)
    )

    retriever.retrieve(fx.project, "How does it compare?", None, quote="5 days")

    assert embedded == ["5 days\nHow does it compare?"]
