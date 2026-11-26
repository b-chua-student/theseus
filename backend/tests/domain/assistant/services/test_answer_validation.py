"""Tests that validation waits no longer than the time left and ignores late results."""

import threading
import time
from uuid import uuid4

import pytest

from domain.assistant.models.errors import AnswerValidationError, ValidationBudgetExceeded
from domain.assistant.models.value_objects import (
    Answer,
    Evidence,
    Finding,
    ProjectId,
    ProposedFinding,
    Query,
    SourceDraft,
    Verdict,
)
from domain.assistant.services.answer_validation import TIMEOUT_MESSAGE, ValidateAnswer
from domain.assistant.services.evidence_retriever import EvidenceRetriever
from tests.domain.assistant.validation_support import (
    QUESTION,
    AcceptingValidator,
    CheckStep,
    FakeClock,
    ScriptedValidator,
    passage,
)

P1 = passage("P1", "The pilot started in May.")


@pytest.mark.parametrize("partial", [False, True])
def test_provider_deadline_returns_only_completed_findings(partial: bool) -> None:  # noqa: FBT001
    clock = FakeClock()
    checks = []
    if partial:
        checks.append(
            CheckStep(Verdict(verified=(Finding("Started in May", 1),), unresolved=("end date",)))
        )
    checks.append(CheckStep(error=ValidationBudgetExceeded("Provider deadline")))
    validator = ScriptedValidator(checks, ["Unchecked revision"], clock)
    answer = ValidateAnswer(validator, EvidenceRetriever(), clock.now).execute(
        question=Query(QUESTION),
        draft=Answer("Unchecked draft"),
        evidence=Evidence((P1,)),
        project_id=ProjectId.from_str(str(uuid4())),
    )
    if partial:
        assert "Started in May [1]" in answer.text
        assert "end date" in answer.text
        assert "Unchecked" not in answer.text
        assert [citation.key for citation in answer.citations] == [1]
    else:
        assert answer == Answer(TIMEOUT_MESSAGE)


class BlockingValidator(AcceptingValidator):
    """Validator whose check blocks until released, then would accept the draft."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.finished = threading.Event()

    def check(self, **_: object) -> Verdict:  # type: ignore[override]
        self.release.wait(timeout=5)
        self.finished.set()
        return Verdict()


def test_s009_a_blocking_check_is_abandoned_at_the_deadline_and_its_result_ignored() -> None:
    validator = BlockingValidator()
    validate = ValidateAnswer(validator, EvidenceRetriever(), time.monotonic, deadline_seconds=0.2)
    started = time.monotonic()

    answer = validate.execute(
        question=Query(QUESTION),
        draft=Answer("The pilot started in May [1]."),
        evidence=Evidence((P1,)),
        project_id=ProjectId.from_str(str(uuid4())),
    )
    waited = time.monotonic() - started
    validator.release.set()
    assert validator.finished.wait(timeout=2)

    assert answer == Answer(TIMEOUT_MESSAGE)
    assert waited < 2


def test_abandoned_calls_are_bounded_and_new_work_is_rejected_until_they_finish() -> None:
    validator = BlockingValidator()
    validate = ValidateAnswer(
        validator,
        EvidenceRetriever(),
        time.monotonic,
        deadline_seconds=0.2,
        max_outstanding_calls=1,
    )

    def run() -> Answer:
        return validate.execute(
            question=Query(QUESTION),
            draft=Answer("The pilot started in May [1]."),
            evidence=Evidence((P1,)),
            project_id=ProjectId.from_str(str(uuid4())),
        )

    assert run() == Answer(TIMEOUT_MESSAGE)
    started = time.monotonic()
    with pytest.raises(AnswerValidationError):
        run()
    assert time.monotonic() - started < 0.15

    validator.release.set()
    assert validator.finished.wait(timeout=2)
    for _ in range(40):
        try:
            answer = run()
            break
        except AnswerValidationError:
            time.sleep(0.05)
    else:
        pytest.fail("The slot was never released")
    assert answer.text == "The pilot started in May [1]."


@pytest.mark.parametrize("arrival", [30.0, 31.0])
def test_s009_late_review_cannot_verify_or_release_unanchored_claims(arrival: float) -> None:
    clock = FakeClock(0.0)
    validator = ScriptedValidator(
        [CheckStep(Verdict(verified=(Finding("Late finding", 1),)), at=arrival)], [], clock
    )
    draft = SourceDraft(
        Answer("Draft"),
        (ProposedFinding(P1.text, 1, P1.text), ProposedFinding("Unanchored", 1, "absent")),
    )
    answer, reusable = ValidateAnswer(validator, EvidenceRetriever(), clock.now).review_draft(
        Query(QUESTION),
        draft,
        Evidence((P1,)),
        ProjectId.from_str(str(uuid4())),
        None,
        "",
        [],
        None,
    )
    assert not reusable
    assert not answer.citations
    assert "Late finding" not in answer.text
    assert answer.unverified_draft and P1.text in answer.unverified_draft
    assert "Unanchored" not in answer.unverified_draft
