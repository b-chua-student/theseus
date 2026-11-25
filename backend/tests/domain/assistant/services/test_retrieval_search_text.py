"""Offline regression tests for S-068: finding evidence without restating the claim (D-003).

Real cosine search runs over hand-built vectors and a fake embedder, so no API is called. The
embedder fails on any search text it was not given a vector for, so each test also proves which
exact text was searched.

Where the numbers come from:

* SESSION-REPORTED values were measured with live Gemini embeddings earlier in the review
  session, and are not re-measured here. They are the cosine between the Methods passage
  "The trial enrolled 18 participants across two sites." and each search text for S-068, and
  the cutoff the calibration script suggested.
* SYNTHETIC values are chosen for these tests. They were never measured against S-068. The
  vectors here are synthetic too: they are built only to reproduce the cosines above.
"""

import math
from dataclasses import dataclass

import pytest

from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import InMemoryVectorStore
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
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
from domain.assistant.services.evidence_retrieval import EvidenceRetriever

# ---- SESSION-REPORTED (live gemini-embedding-001, S-068, Methods passage) ----
SESSION_QUESTION_ONLY = 0.656
SESSION_QUESTION_PLUS_DRAFT = 0.827
SESSION_SUGGESTED_CUTOFF = 0.6904  # from scripts/calibrate_relevance_threshold.py

# ---- SYNTHETIC (invented for these tests; never measured against S-068) ----
SYNTHETIC_REPLICATION = 0.80
SYNTHETIC_SAME_TOPIC_BELOW_CUTOFF = 0.62
SYNTHETIC_SAME_TOPIC_ABOVE_CUTOFF = 0.70
SYNTHETIC_LOW_SCORING = 0.30

QUESTION = "Which selected studies support my enrollment figure?"
DRAFT = "The trial enrolled 18 participants."
WITH_DRAFT = f"{QUESTION}\n{DRAFT}"

E1, E2, E3 = [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]


def at_cosine(reference: list[float], target: float, perpendicular: list[float]) -> list[float]:
    """Return a unit vector whose cosine to ``reference`` is ``target``.

    ``reference`` and ``perpendicular`` must be orthogonal unit vectors.
    """
    rest = math.sqrt(1 - target**2)
    return [target * r + rest * p for r, p in zip(reference, perpendicular, strict=True)]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


# The question-plus-draft search text is the reference axis.
VECTOR_WITH_DRAFT = E1
METHODS_PASSAGE = at_cosine(E1, SESSION_QUESTION_PLUS_DRAFT, E2)
# E3 is orthogonal to the Methods passage, so this reproduces the question-only cosine.
VECTOR_QUESTION_ONLY = at_cosine(METHODS_PASSAGE, SESSION_QUESTION_ONLY, E3)


class StrictEmbedder(EmbeddingGenerator):
    """Embeds only the texts it knows, and records every text it is asked to embed."""

    def __init__(self, table: dict[str, list[float]]) -> None:
        self.table = table
        self.inputs: list[str] = []

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        self.inputs.extend(chunk.text for chunk in chunks)
        return [Embedding(chunk.id, self.table[chunk.text]) for chunk in chunks]


class SpyStore(InMemoryVectorStore):
    """In-memory cosine store that records what each search asked for and found."""

    def __init__(self) -> None:
        super().__init__()
        self.searched: list[DocumentRefId] = []
        self.found: dict[DocumentRefId, list[RetrievedChunk]] = {}

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        results = super().query(query_embedding, k, doc_ref_ids)
        for ref in doc_ref_ids or []:
            self.searched.append(ref)
            self.found[ref] = [chunk for chunk in results if chunk.doc_ref_id == ref]
        return results


@dataclass
class Setup:
    project: ProjectId
    store: SpyStore
    documents: InMemoryIndexedDocumentRepository
    active: list[DocumentRefId]
    refs: dict[str, DocumentRefId]

    def source(self, title: str, passage: str, vector: list[float]) -> DocumentRefId:
        ref = DocumentRefId.new()
        document = IndexedDocument.create(IndexedDocumentTitle(title), ref, self.project)
        chunk = Chunk(ChunkId.new(), passage, "1", "p1", content_hash=passage)
        document.start_indexing()
        document.complete_indexing([chunk])
        self.documents.add(document)
        self.store.upsert(ref, [Embedding(chunk.id, vector)], [chunk])
        self.active.append(ref)
        self.refs[title] = ref
        return ref

    def retriever(
        self, embedder: EmbeddingGenerator, cutoff: float | None = SESSION_SUGGESTED_CUTOFF
    ) -> EvidenceRetriever:
        return EvidenceRetriever(
            embedder,
            self.store,
            self.documents,
            lambda _project: list(self.active),
            relevance_threshold=cutoff,
        )


@pytest.fixture
def setup() -> Setup:
    return Setup(ProjectId.new(), SpyStore(), InMemoryIndexedDocumentRepository(), [], {})


def both_texts() -> StrictEmbedder:
    return StrictEmbedder({QUESTION: VECTOR_QUESTION_ONLY, WITH_DRAFT: VECTOR_WITH_DRAFT})


def statuses(evidence) -> dict[str, SourceStatus]:  # noqa: ANN001
    return {outcome.title: outcome.status for outcome in evidence.outcomes}


def test_the_fixture_vectors_reproduce_the_session_reported_cosines() -> None:
    assert cosine(VECTOR_WITH_DRAFT, METHODS_PASSAGE) == pytest.approx(0.827)
    assert cosine(VECTOR_QUESTION_ONLY, METHODS_PASSAGE) == pytest.approx(0.656)
    assert SESSION_QUESTION_ONLY < SESSION_SUGGESTED_CUTOFF <= SESSION_QUESTION_PLUS_DRAFT


def test_a_study_reporting_the_figure_is_found_without_restating_the_claim(setup: Setup) -> None:
    methods = setup.source(
        "Methods", "The trial enrolled 18 participants across two sites.", METHODS_PASSAGE
    )
    replication = setup.source(
        "Replication",
        "In the replication, the same trial enrolled 24 participants.",
        at_cosine(E1, SYNTHETIC_REPLICATION, E3),
    )
    setup.source("Pilot", "The pilot study enrolled 18 participants.", METHODS_PASSAGE)
    embedder = both_texts()

    evidence = setup.retriever(embedder).retrieve(
        setup.project, QUESTION, [str(methods.value), str(replication.value)], draft=DRAFT
    )

    assert embedder.inputs == [WITH_DRAFT]
    assert sorted(chunk.title for chunk in evidence.excerpts) == ["Methods", "Replication"]
    assert evidence.outcomes == []
    assert setup.refs["Pilot"] not in setup.store.searched


def test_the_same_question_does_not_find_it_when_the_draft_is_not_searched(setup: Setup) -> None:
    methods = setup.source(
        "Methods", "The trial enrolled 18 participants across two sites.", METHODS_PASSAGE
    )
    embedder = both_texts()

    evidence = setup.retriever(embedder).retrieve(
        setup.project, QUESTION, [str(methods.value)], draft=None
    )

    assert embedder.inputs == [QUESTION]
    assert evidence.excerpts == []
    assert statuses(evidence) == {"Methods": SourceStatus.SEARCHED_WITHOUT_MATCH}


def test_a_same_topic_study_that_never_reports_the_figure_is_left_out(setup: Setup) -> None:
    methods = setup.source(
        "Methods",
        "Outcome assessors were blinded to treatment allocation.",
        at_cosine(E1, SYNTHETIC_SAME_TOPIC_BELOW_CUTOFF, E2),
    )

    evidence = setup.retriever(both_texts()).retrieve(
        setup.project, QUESTION, [str(methods.value)], draft=DRAFT
    )

    assert evidence.excerpts == []
    assert statuses(evidence) == {"Methods": SourceStatus.SEARCHED_WITHOUT_MATCH}


def test_a_source_with_no_passage_at_the_cutoff_is_not_refilled_with_its_best_ones(
    setup: Setup,
) -> None:
    methods = setup.source(
        "Methods",
        "Outcome assessors were blinded to treatment allocation.",
        at_cosine(E1, SYNTHETIC_SAME_TOPIC_BELOW_CUTOFF, E2),
    )

    evidence = setup.retriever(both_texts()).retrieve(
        setup.project, QUESTION, [str(methods.value)], draft=DRAFT
    )

    # The store did rank the passage, so it was the cutoff that removed it, not its absence.
    assert [chunk.score for chunk in setup.store.found[methods]] == [
        pytest.approx(SYNTHETIC_SAME_TOPIC_BELOW_CUTOFF)
    ]
    assert evidence.excerpts == []


def test_known_limit_a_same_topic_passage_above_the_cutoff_still_reaches_the_model(
    setup: Setup,
) -> None:
    methods = setup.source(
        "Methods",
        "Outcome assessors were blinded to treatment allocation.",
        at_cosine(E1, SYNTHETIC_SAME_TOPIC_ABOVE_CUTOFF, E2),
    )

    evidence = setup.retriever(both_texts()).retrieve(
        setup.project, QUESTION, [str(methods.value)], draft=DRAFT
    )

    # Retrieval cannot tell this from a relevant passage at this score; recalibration is open.
    assert [chunk.title for chunk in evidence.excerpts] == ["Methods"]


def test_known_limit_with_no_cutoff_set_a_low_scoring_passage_is_still_admitted(
    setup: Setup,
) -> None:
    methods = setup.source(
        "Methods",
        "Quarterly revenue rose three percent.",
        at_cosine(E1, SYNTHETIC_LOW_SCORING, E2),
    )

    evidence = setup.retriever(both_texts(), cutoff=None).retrieve(
        setup.project, QUESTION, [str(methods.value)], draft=DRAFT
    )

    # The production cutoff is unset, so "searched without a match" cannot happen there yet.
    assert [chunk.title for chunk in evidence.excerpts] == ["Methods"]
    assert evidence.outcomes == []


def test_with_a_quote_the_search_text_is_the_quote_then_the_question_without_the_draft(
    setup: Setup,
) -> None:
    quote = "Children recovered in 5 days"
    question = "How does this passage compare with Methods?"
    draft = "Adults recovered in 8 days. Children recovered in 5 days."
    methods = setup.source("Methods", "Children recovered in 7 days.", METHODS_PASSAGE)
    embedder = StrictEmbedder({f"{quote}\n{question}": VECTOR_WITH_DRAFT})

    evidence = setup.retriever(embedder).retrieve(
        setup.project, question, [str(methods.value)], quote=quote, draft=draft
    )

    assert embedder.inputs == [f"{quote}\n{question}"]
    assert [chunk.title for chunk in evidence.excerpts] == ["Methods"]


def test_with_manuscript_unchecked_no_draft_text_is_searched_with_or_without_a_quote(
    setup: Setup,
) -> None:
    methods = setup.source("Methods", "Children recovered in 7 days.", METHODS_PASSAGE)
    quote = "Children recovered in 5 days"
    embedder = StrictEmbedder(
        {QUESTION: VECTOR_QUESTION_ONLY, f"{quote}\n{QUESTION}": VECTOR_WITH_DRAFT}
    )
    retriever = setup.retriever(embedder)

    retriever.retrieve(setup.project, QUESTION, [str(methods.value)], draft=None)
    retriever.retrieve(setup.project, QUESTION, [str(methods.value)], quote=quote, draft=None)

    assert embedder.inputs == [QUESTION, f"{quote}\n{QUESTION}"]
