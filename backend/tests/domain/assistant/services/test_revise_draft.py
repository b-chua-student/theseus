"""Tests for revising a draft against the admitted evidence."""

from domain.assistant.models.value_objects import Answer, Evidence, Finding, Query, Verdict
from domain.assistant.services.revise_draft import ReviseDraft
from tests.domain.assistant.validation_support import (
    QUESTION,
    FakeClock,
    ScriptedValidator,
    passage,
)

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
MAY = Finding("The pilot started in May", 1)


def reviser(revisions: list[str]) -> tuple[ReviseDraft, ScriptedValidator]:
    validator = ScriptedValidator([], revisions, FakeClock())
    return ReviseDraft(validator), validator


def test_s004_a_corrected_citation_resolves_to_the_passage_that_supports_it() -> None:
    corrected = "The pilot started in May [1] and ended in July [2]."
    verdict = Verdict(verified=(MAY,), unresolved=("July end cites P1, not P2",))
    revise, validator = reviser([corrected])

    revised = revise.execute(
        question=Query(QUESTION),
        answer=Answer("The pilot started in May [1] and ended in July [1]."),
        verdict=verdict,
        evidence=Evidence((P1, P2)),
    )

    assert revised.text == corrected
    assert [(c.key, c.location) for c in revised.citations] == [(1, "P1"), (2, "P2")]
    [call] = validator.revisions
    assert call.question == QUESTION
    assert call.verdict == verdict
    assert [p.chunk_id for p in call.passages] == [P1.chunk_id, P2.chunk_id]


def test_s003_a_revision_that_drops_a_claim_drops_its_citation() -> None:
    revise, _ = reviser(["The pilot started in May [1]."])

    revised = revise.execute(
        question=Query(QUESTION),
        answer=Answer("The pilot started in May [1] and ended on July 12 [2]."),
        verdict=Verdict(unresolved=("ended on July 12",)),
        evidence=Evidence((P1, P2)),
    )

    assert [c.key for c in revised.citations] == [1]


def test_s005_a_revision_after_a_new_search_cites_retained_and_new_passages() -> None:
    revise, validator = reviser(["The pilot started in May [1] and ended in July [2]."])
    evidence = Evidence((P1,)).merge([P2, P1], limit=5)

    revised = revise.execute(
        question=Query(QUESTION),
        answer=Answer("The pilot started in May [1]."),
        verdict=Verdict(missing_evidence="when the pilot ended"),
        evidence=evidence,
    )

    assert [(c.key, c.location) for c in revised.citations] == [(1, "P1"), (2, "P2")]
    assert [p.location for p in validator.revisions[0].passages] == ["P1", "P2"]


def test_a_revision_citing_a_passage_that_was_not_admitted_does_not_cite_it() -> None:
    revise, _ = reviser(["The pilot started in May [1] and ended in July [7]."])

    revised = revise.execute(
        question=Query(QUESTION),
        answer=Answer("The pilot started in May [1]."),
        verdict=Verdict(unresolved=("x",)),
        evidence=Evidence((P1,)),
    )

    assert [c.key for c in revised.citations] == [1]


def test_s012_the_manuscript_text_reaches_the_validator() -> None:
    revise, validator = reviser(["The manuscript says July 12; the report gives July [1]."])

    revise.execute(
        question=Query(QUESTION),
        answer=Answer("The report contradicts the manuscript [1]."),
        verdict=Verdict(unresolved=("report contradicts the manuscript",)),
        evidence=Evidence((P1,)),
        manuscript_text="The pilot ended on July 12.",
    )

    assert validator.revisions[0].manuscript_text == "The pilot ended on July 12."
