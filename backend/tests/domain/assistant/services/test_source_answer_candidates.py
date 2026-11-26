"""Offline component checks for local selection, assisted verification and recovery."""

from unittest.mock import Mock

from domain.assistant.infrastructure.ports.answer_validator import AnswerProposer
from domain.assistant.models.value_objects import Evidence, ProposedFinding, Query
from domain.assistant.services.source_answer_candidates import SourceAnswerCandidates
from tests.domain.assistant.validation_support import QUESTION, passage

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
