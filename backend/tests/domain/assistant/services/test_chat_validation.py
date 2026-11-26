"""Scenario tests for validating source-backed answers (gherkin.feature S-001 to S-013).

The validation contract these tests assume is documented in ``validation_support``.
"""

import pytest

from domain.assistant.models.errors import ChatModelError
from domain.assistant.models.value_objects import Answer
from tests.domain.assistant.validation_support import (
    DEADLINE,
    INTERRUPTED_MESSAGE,
    OFF_TOPIC_MESSAGE,
    QUESTION,
    START,
    TIMEOUT_MESSAGE,
    CheckStep,
    Env,
    Finding,
    QueryStep,
    Verdict,
    build,
    passage,
)

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")

MAY = Finding("The pilot started in May", 1)
PASS = Verdict()
SUPPORTED = "The pilot started in May [1] and ended in July [2]."


def ask(env: Env, manuscript_text: str = "") -> Answer:
    return env.service.ask(
        env.conversation_id,
        QUESTION,
        context_scope="source_library",
        manuscript_text=manuscript_text,
    )


def cited(answer: Answer) -> list[tuple[int, str]]:
    return [(c.key, c.location) for c in answer.citations]  # type: ignore[attr-defined]


def recorded(env: Env) -> list[str]:
    conversation = env.service.get(env.project_id, env.conversation_id)
    return [e.answer.text for e in conversation.history if e.answer is not None]


def test_s001_displays_a_supported_answer_after_checking_it() -> None:
    env = build(drafts=[SUPPORTED], searches=[QueryStep([P1, P2])], checks=[CheckStep(PASS)])

    answer = ask(env)

    assert answer.text == SUPPORTED
    assert cited(answer) == [(1, "P1"), (2, "P2")]
    [check] = env.validator.checks
    assert (check.question, check.text) == (QUESTION, SUPPORTED)
    assert [p.location for p in check.passages] == ["P1", "P2"]
    assert env.validator.revisions == []
    assert recorded(env) == [SUPPORTED]


def test_s002_withholds_a_draft_that_answers_a_different_question() -> None:
    sponsor_only = "The pilot was sponsored by the university [1]."
    p3 = passage("P3", "The pilot was sponsored by the university.")
    env = build(
        drafts=[sponsor_only],
        searches=[QueryStep([P1, p3])],
        checks=[CheckStep(Verdict(relevant=False)), CheckStep(PASS)],
        revisions=["The pilot started in May [1]."],
    )

    answer = ask(env)

    assert "sponsor" not in answer.text
    assert env.validator.checks[0].text == sponsor_only
    assert recorded(env) == [answer.text]


def test_s003_revises_an_overstated_claim_and_checks_the_revision() -> None:
    overstated = "The pilot started in May [1] and ended on July 12 [2]."
    revised = "The pilot started in May [1] and ended in July [2]."
    unsupported = Verdict(verified=(MAY,), unresolved=("ended on July 12",))
    env = build(
        drafts=[overstated],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(unsupported), CheckStep(PASS)],
        revisions=[revised],
    )

    answer = ask(env)

    assert answer.text == revised
    assert "12" not in answer.text
    [revision] = env.validator.revisions
    assert (revision.text, revision.verdict) == (overstated, unsupported)
    assert [c.text for c in env.validator.checks] == [overstated, revised]
    assert recorded(env) == [revised]


def test_s004_corrects_a_mismatched_citation_and_checks_the_correction() -> None:
    mismatched = "The pilot started in May [1] and ended in July [1]."
    corrected = "The pilot started in May [1] and ended in July [2]."
    wrong_target = Verdict(verified=(MAY,), unresolved=("July end cites P1, not P2",))
    env = build(
        drafts=[mismatched],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(wrong_target), CheckStep(PASS)],
        revisions=[corrected],
    )

    answer = ask(env)

    assert answer.text == corrected
    assert cited(answer) == [(1, "P1"), (2, "P2")]
    assert env.validator.checks[-1].text == corrected
    assert recorded(env) == [corrected]


def test_s005_searches_again_for_missing_evidence_and_checks_against_all_passages() -> None:
    first_draft = "The pilot started in May [1]."
    missing_end = Verdict(
        verified=(MAY,), unresolved=("end date",), missing_evidence="when the pilot ended"
    )
    env = build(
        drafts=[first_draft],
        searches=[QueryStep([P1]), QueryStep([P2, P1])],
        checks=[CheckStep(missing_end), CheckStep(PASS)],
        revisions=[SUPPORTED],
    )

    answer = ask(env)

    assert answer.text == SUPPORTED
    assert cited(answer) == [(1, "P1"), (2, "P2")]
    assert env.embedder.texts[0] == QUESTION
    assert QUESTION in env.embedder.texts[1]
    assert "when the pilot ended" in env.embedder.texts[1]
    first_scope, second_scope = env.store.searched_documents
    assert first_scope == second_scope
    [revision] = env.validator.revisions
    assert [p.chunk_id for p in revision.passages] == [P1.chunk_id, P2.chunk_id]
    assert [p.chunk_id for p in env.validator.checks[-1].passages] == [P1.chunk_id, P2.chunk_id]
    assert env.validator.checks[-1].text == SUPPORTED


def test_s006_stops_at_the_retry_limit_and_explains_the_remaining_gap() -> None:
    overstated = "The pilot started in May [1] and ended on July 12 [1]."
    still_wrong = "The pilot started in May [1] and probably ended on July 12 [1]."
    no_end_date = Verdict(
        verified=(MAY,),
        unresolved=("end date",),
        gaps=("end date",),
        missing_evidence="when the pilot ended",
    )
    env = build(
        drafts=[overstated],
        searches=[QueryStep([P1]), QueryStep([P1])],
        checks=[
            CheckStep(Verdict(verified=(MAY,), unresolved=("ended on July 12",))),
            CheckStep(no_end_date),
            CheckStep(no_end_date),
        ],
        revisions=[still_wrong, "The pilot started in May [1]; the end date is unknown."],
    )

    answer = ask(env)

    assert len(env.validator.checks) == 3
    assert len(env.validator.revisions) == 2
    assert len(env.store.searched_documents) == 2
    assert cited(answer) == [(1, "P1")]
    assert "May" in answer.text
    assert "end date" in answer.text.lower()
    assert "July 12" not in answer.text
    assert recorded(env) == [answer.text]


def test_s008_returns_verified_findings_when_the_deadline_cuts_a_retry_short() -> None:
    draft = "The pilot started in May [1] and ended on July 12 [1]."
    unresolved_end = Verdict(
        verified=(MAY,), unresolved=("end date",), missing_evidence="when the pilot ended"
    )
    env = build(
        drafts=[draft],
        searches=[QueryStep([P1]), QueryStep([P1, P2], at=DEADLINE + 1)],
        checks=[CheckStep(unresolved_end)],
    )

    answer = ask(env)

    assert cited(answer) == [(1, "P1")]
    assert "May" in answer.text
    assert "end date" in answer.text.lower()
    assert "in time" in answer.text
    assert "July 12" not in answer.text
    assert len(env.validator.checks) == 1
    assert env.validator.revisions == []
    assert recorded(env) == [answer.text]


def test_s009_reports_a_timeout_when_no_check_finishes_in_time() -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(PASS, at=DEADLINE + 1)],
    )

    answer = ask(env)

    assert answer.text == TIMEOUT_MESSAGE
    assert cited(answer) == []
    assert recorded(env) == [TIMEOUT_MESSAGE]


def test_s009_the_deadline_starts_when_the_first_draft_is_ready() -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(PASS, at=START + 40)],
        draft_takes=20.0,
    )

    answer = ask(env)

    assert answer.text == SUPPORTED


def test_s010_reports_off_topic_drafts_without_claiming_a_source_gap() -> None:
    sponsor_only = "The pilot was sponsored by the university [1]."
    off_topic = Verdict(relevant=False)
    env = build(
        drafts=[sponsor_only],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(off_topic), CheckStep(off_topic), CheckStep(off_topic)],
        revisions=["The sponsor was the university [1].", "The university sponsored it [1]."],
    )

    answer = ask(env)

    assert answer.text == OFF_TOPIC_MESSAGE
    assert len(env.validator.checks) == 3
    assert len(env.validator.revisions) == 2
    assert len(env.store.searched_documents) == 1
    assert recorded(env) == [OFF_TOPIC_MESSAGE]


def test_s011_withholds_the_draft_when_a_service_error_interrupts_the_check() -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(error=RuntimeError("validator down"), at=START + 3)],
    )

    with pytest.raises(ChatModelError) as raised:
        ask(env)

    assert str(raised.value) == INTERRUPTED_MESSAGE
    assert env.service.get(env.project_id, env.conversation_id).exchanges == []


def test_s012_attributes_the_manuscript_claim_and_flags_the_unverified_day() -> None:
    manuscript = "The pilot ended on July 12."
    contradiction = "The report contradicts the manuscript, which says July 12 [1]."
    revised = (
        "The manuscript says the pilot ended on July 12. The report gives July [2] without "
        "a day, so the exact day is unverified."
    )
    omission_only = Verdict(unresolved=("report contradicts the manuscript",))
    env = build(
        drafts=[contradiction],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(omission_only), CheckStep(PASS)],
        revisions=[revised],
    )

    answer = ask(env, manuscript_text=manuscript)

    assert answer.text == revised
    assert [c.manuscript_text for c in env.validator.checks] == [manuscript, manuscript]
    assert env.validator.revisions[0].manuscript_text == manuscript
    assert env.validator.revisions[0].verdict == omission_only
    assert env.validator.checks[-1].text == revised
    assert recorded(env) == [revised]


@pytest.mark.parametrize(
    "verified",
    [
        pytest.param((MAY,), id="with-verified-findings"),
        pytest.param((), id="without-verified-findings"),
    ],
)
def test_s013_a_service_error_at_the_deadline_gets_the_deadline_response(
    verified: tuple[Finding, ...],
) -> None:
    draft = "The pilot started in May [1] and ended on July 12 [1]."
    failing_at_deadline = CheckStep(error=RuntimeError("validator down"), at=DEADLINE)
    if verified:
        checks = [
            CheckStep(Verdict(verified=verified, unresolved=("end date",))),
            failing_at_deadline,
        ]
        revisions = ["The pilot started in May [1] and ended in July."]
    else:
        checks, revisions = [failing_at_deadline], []
    env = build(drafts=[draft], searches=[QueryStep([P1])], checks=checks, revisions=revisions)

    answer = ask(env)

    assert "July 12" not in answer.text
    if verified:
        assert cited(answer) == [(1, "P1")]
        assert "May" in answer.text
        assert "end date" in answer.text.lower()
        assert "in time" in answer.text
    else:
        assert answer.text == TIMEOUT_MESSAGE
        assert cited(answer) == []
    assert recorded(env) == [answer.text]
