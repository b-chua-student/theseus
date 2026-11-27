"""Tests for finding more evidence within the request's source scope."""

from uuid import uuid4

import pytest

from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.models.errors import RetrievalError
from domain.assistant.models.value_objects import Answer, Evidence, ProjectId, Query, Verdict
from domain.assistant.services.evidence_retriever import EvidenceRetriever
from domain.assistant.services.revise_draft import ReviseDraft
from tests.domain.assistant.validation_support import (
    QUESTION,
    FakeClock,
    QueryStep,
    RecordingEmbedder,
    ScriptedValidator,
    ScriptedVectorStore,
    passage,
    searchable_document,
)

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
P3 = passage("P3", "The pilot was sponsored by the university.")
MISSING = "when the pilot ended"


class Setup:
    def __init__(self, searches: list[QueryStep], top_k: int = 5) -> None:
        self.project_id = ProjectId.from_str(str(uuid4()))
        self.documents = InMemoryIndexedDocumentRepository()
        self.first = searchable_document(self.project_id)
        self.second = searchable_document(self.project_id)
        self.documents.add(self.first)
        self.documents.add(self.second)
        self.store = ScriptedVectorStore(searches, FakeClock())
        self.embedder = RecordingEmbedder()
        self.retriever = EvidenceRetriever(
            embedding_generator=self.embedder,
            vector_store=self.store,
            document_repository=self.documents,
            source_ids=lambda _project: [self.first.doc_ref_id, self.second.doc_ref_id],
            top_k=top_k,
        )


def test_search_embeds_the_text_and_returns_the_passages() -> None:
    setup = Setup([QueryStep([P1])])

    found = setup.retriever.search(setup.project_id, QUESTION)

    assert found == [P1]
    assert setup.embedder.texts == [QUESTION]


def test_search_is_limited_to_the_selected_sources() -> None:
    setup = Setup([QueryStep([P1])])
    selected = str(setup.second.doc_ref_id.value)

    setup.retriever.search(setup.project_id, QUESTION, [selected])

    assert setup.store.searched_documents == [[setup.second.doc_ref_id]]


def test_search_without_searchable_sources_finds_nothing_and_does_not_query() -> None:
    setup = Setup([])

    assert setup.retriever.search(setup.project_id, QUESTION, [str(uuid4())]) == []
    assert setup.store.searched_documents == []


def test_search_without_retrieval_ports_finds_nothing() -> None:
    retriever = EvidenceRetriever()

    assert retriever.search(ProjectId.from_str(str(uuid4())), QUESTION) == []


def test_s107_an_empty_result_is_not_a_failed_lookup() -> None:
    setup = Setup([QueryStep([])])

    assert setup.retriever.search(setup.project_id, QUESTION) == []


def test_s108_a_failed_lookup_raises_a_retrieval_error() -> None:
    setup = Setup([QueryStep(error=RuntimeError("vector store down"))])

    with pytest.raises(RetrievalError) as raised:
        setup.retriever.search(setup.project_id, QUESTION)

    assert isinstance(raised.value.__cause__, RuntimeError)


def test_s102_find_more_searches_for_the_original_question_and_the_missing_evidence() -> None:
    setup = Setup([QueryStep([P2, P1])])

    setup.retriever.find_more(setup.project_id, Query(QUESTION), Evidence((P1,)), MISSING)

    [text] = setup.embedder.texts
    assert QUESTION in text
    assert MISSING in text


def test_s102_find_more_uses_the_same_source_scope_as_the_first_search() -> None:
    setup = Setup([QueryStep([P1]), QueryStep([P2, P1])])
    selected = [str(setup.first.doc_ref_id.value)]

    setup.retriever.search(setup.project_id, QUESTION, selected)
    setup.retriever.find_more(setup.project_id, Query(QUESTION), Evidence((P1,)), MISSING, selected)

    first_scope, second_scope = setup.store.searched_documents
    assert first_scope == second_scope == [setup.first.doc_ref_id]


def test_s102_find_more_keeps_retained_passages_and_adds_the_new_one() -> None:
    setup = Setup([QueryStep([P2, P1])])

    evidence = setup.retriever.find_more(
        setup.project_id, Query(QUESTION), Evidence((P1,)), MISSING
    )

    assert [p.chunk_id for p in evidence.passages] == [P1.chunk_id, P2.chunk_id]


def test_find_more_keeps_each_revised_draft_within_the_evidence_budget() -> None:
    setup = Setup([QueryStep([P3, P2])], top_k=2)

    evidence = setup.retriever.find_more(
        setup.project_id, Query(QUESTION), Evidence((P1,)), MISSING
    )

    assert [p.location for p in evidence.passages] == ["P1", "P3"]


def test_find_more_without_a_missing_evidence_description_searches_the_question() -> None:
    setup = Setup([QueryStep([P1])])

    setup.retriever.find_more(setup.project_id, Query(QUESTION), Evidence(), None)

    assert setup.embedder.texts == [QUESTION]


def test_s108_find_more_raises_a_retrieval_error_and_leaves_the_evidence_untouched() -> None:
    setup = Setup([QueryStep(error=RuntimeError("vector store down"))])
    evidence = Evidence((P1,))

    with pytest.raises(RetrievalError):
        setup.retriever.find_more(setup.project_id, Query(QUESTION), evidence, MISSING)

    assert evidence.passages == (P1,)


def test_s102_a_full_first_search_still_admits_the_missing_end_date() -> None:
    start = passage("P1", "The pilot started in May.")
    unrelated_a = passage("P4", "The pilot site was a hospital.")
    unrelated_b = passage("P5", "The pilot enrolled forty patients.")
    end = passage("P2", "The pilot ended in July.")
    setup = Setup([QueryStep([end])], top_k=3)
    first_search = Evidence((start, unrelated_a, unrelated_b))
    draft = Answer("The pilot started in May [1].")
    cited_keys = [c.key for c in first_search.citations_for(draft.text)]
    validator = ScriptedValidator(
        [], ["The pilot started in May [1] and ended in July [3]."], FakeClock()
    )

    evidence = setup.retriever.find_more(
        setup.project_id, Query(QUESTION), first_search, MISSING, keep=cited_keys
    )
    revised = ReviseDraft(validator).execute(
        question=Query(QUESTION),
        answer=draft,
        verdict=Verdict(missing_evidence=MISSING),
        evidence=evidence,
    )

    sent = [p.chunk_id for p in validator.revisions[0].passages]
    cited = {c.key: c.chunk_id for c in revised.citations}
    assert end.chunk_id in sent
    assert cited[1] == start.chunk_id
    assert cited[3] == end.chunk_id
    assert len(sent) <= 3
    assert sent[1] == unrelated_a.chunk_id
