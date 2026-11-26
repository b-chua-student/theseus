"""Tests that validation waits no longer than the time left and ignores late results."""

import threading
import time
from uuid import uuid4

import pytest

from domain.assistant.models.errors import AnswerValidationError
from domain.assistant.models.value_objects import Answer, Evidence, ProjectId, Query, Verdict
from domain.assistant.services.answer_validation import TIMEOUT_MESSAGE, ValidateAnswer
from domain.assistant.services.evidence_retriever import EvidenceRetriever
from tests.domain.assistant.validation_support import (
    QUESTION,
    AcceptingValidator,
    passage,
)

P1 = passage("P1", "The pilot started in May.")


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
