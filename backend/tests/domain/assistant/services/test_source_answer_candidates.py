"""Offline component checks for local selection, assisted verification and recovery."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.assistant.infrastructure.ports.answer_validator import AnswerProposer
from domain.assistant.models.errors import ValidationBudgetExceeded
from domain.assistant.models.value_objects import (
    Answer,
    Evidence,
    ProjectId,
    ProposedFinding,
    Query,
)
from domain.assistant.services.answer_validation import ValidateAnswer
from domain.assistant.services.evidence_retriever import EvidenceRetriever
from domain.assistant.services.source_answer_candidates import SourceAnswerCandidates
from tests.domain.assistant.validation_support import QUESTION, FakeClock, passage

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
P3 = passage("P3", "Follow-up ended in August.")


def test_s014_s005_local_revision_after_search_uses_no_generation() -> None:
    provider = Mock(spec=AnswerProposer)
    candidates = SourceAnswerCandidates(provider)
    evidence = Evidence((P1,))
    partial, first = candidates.local(Query(QUESTION), evidence)
    assert not first.passed
    assert "May [1]" in partial.text
    answer, checked = candidates.local(Query(QUESTION), evidence.merge([P2], 2))
    assert checked.passed
    assert "May [1]" in answer.text and "July [2]" in answer.text
    provider.propose.assert_not_called()


def test_s015_assisted_selection_locally_checks_each_claim_and_excerpt() -> None:
    provider = Mock(spec=AnswerProposer)
    candidates = SourceAnswerCandidates(provider)
    evidence = Evidence((P1, P2, P3))
    _, first = candidates.local(Query(QUESTION), evidence)
    assert not first.passed
    provider.propose.return_value = (
        ProposedFinding(P1.text, 1, P1.text),
        ProposedFinding(P2.text, 2, P2.text),
    )
    answer, result = candidates.assisted(Query(QUESTION), evidence)
    assert result.passed
    assert [c.location for c in answer.citations] == ["P1", "P2"]
    assert "August" not in answer.text
    provider.propose.assert_called_once()


def test_s004_s016_wrong_citation_and_added_precision_are_withheld() -> None:
    provider = Mock(spec=AnswerProposer)
    provider.propose.return_value = (
        ProposedFinding(P1.text, 2, P1.text),
        ProposedFinding("The pilot ended in 2025.", 2, P2.text),
    )
    candidates = SourceAnswerCandidates(provider)
    question = Query("In what year did the pilot end?")
    answer, verdict = candidates.assisted(question, Evidence((P1, P2)))
    assert not verdict.passed and not answer.citations
    assert "2025" not in answer.text
    revised, verdict = candidates.local(question, Evidence((P1, P2)))
    assert not verdict.passed and "year" in revised.text
    assert [c.location for c in revised.citations] == ["P2"]
    provider.propose.assert_called_once()


def test_s012_local_revision_separates_manuscript_day_from_library_month() -> None:
    answer, verdict = SourceAnswerCandidates(None).local(
        Query("Did the pilot end on July 12?"), Evidence((P2,)), "The pilot ended on July 12."
    )
    assert not verdict.passed
    assert "July [1]" in answer.text
    assert "The manuscript states: The pilot ended on July 12." in answer.text
    assert "Could not verify" in answer.text


def test_conflicting_source_dates_are_withheld() -> None:
    evidence = Evidence((P2, passage("P4", "The pilot ended in August.")))
    answer, verdict = SourceAnswerCandidates(None).local(Query("When did the pilot end?"), evidence)
    assert not verdict.passed and not answer.citations


def test_s004_swapped_passages_cannot_verify_either_claim() -> None:
    provider = Mock(spec=AnswerProposer)
    provider.propose.return_value = (
        ProposedFinding(P1.text, 2, P1.text),
        ProposedFinding(P2.text, 1, P2.text),
    )
    answer, verdict = SourceAnswerCandidates(provider).assisted(Query(QUESTION), Evidence((P1, P2)))
    assert not verdict.passed and not verdict.verified and not answer.citations


def test_an_explicit_attribute_can_be_answered_without_generation() -> None:
    evidence = Evidence((passage("Report", "The budget of the study was $300."),))
    answer, verdict = SourceAnswerCandidates(None).local(
        Query("What was the budget of the study?"), evidence
    )
    assert verdict.passed and "$300 [1]" in answer.text


def test_s018_deadline_between_claim_checks_offers_only_pending_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = Mock(spec=AnswerProposer)
    provider.propose.return_value = (
        ProposedFinding("The pilot started on July 12.", 1, P1.text),
        ProposedFinding(P2.text, 2, P2.text),
    )
    # Competing events keep the initial local pass inconclusive for both dates.
    evidence = Evidence((P1, P2, P3, passage("P4", "Follow-up started in April.")))

    def expire_during_precision_check(value: str, detail: str) -> bool:
        assert value == "july"
        raise ValidationBudgetExceeded("Deadline during the second claim check")

    monkeypatch.setattr(
        "domain.assistant.services.local_evidence._sufficient", expire_during_precision_check
    )
    answer = ValidateAnswer(None, EvidenceRetriever(), FakeClock().now).execute(
        question=Query(QUESTION),
        draft=Answer("Waiting for evidence checks."),
        evidence=evidence,
        project_id=ProjectId.from_str(str(uuid4())),
        candidates=SourceAnswerCandidates(provider),
    )
    provider.propose.assert_called_once()
    assert not answer.citations
    assert P2.text not in answer.text and "July 12" not in answer.text
    draft = getattr(answer, "unverified_draft", None)
    assert draft and P2.text in draft
    assert "July 12" not in draft
