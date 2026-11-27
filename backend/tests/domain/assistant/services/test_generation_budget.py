"""Count all provider attempts through a source-backed exchange (S-111 to S-120)."""

import json
from unittest.mock import patch

import pytest
from google.genai import errors as genai_errors

from domain.assistant.models.errors import ChatModelError
from tests.domain.assistant.generation_support import END, START, exchange, proposal, reviewed
from tests.domain.assistant.validation_support import INTERRUPTED_MESSAGE, QUESTION, TIMEOUT_MESSAGE


def test_s112_review_corrects_group_size_to_total() -> None:
    excerpt = "There were 75 schools overall and 25 schools in each group."
    wrong = "There were 25 schools overall."
    corrected = "There were 75 schools overall."
    draft = json.dumps(
        {"answer": wrong + " [1]", "claims": [{"text": wrong, "citation": 1, "excerpt": excerpt}]}
    )
    with exchange(
        [[excerpt], [excerpt], [excerpt]], [draft, reviewed((corrected, 1, excerpt))], 2
    ) as env:
        answer = env.service.ask(env.conversation_id, "How many schools enrolled overall?")
        assert "75" in answer.text and wrong not in answer.text
        assert [(c.key, c.location) for c in answer.citations] == [(1, "P1")]


def test_s113_year_is_withheld_after_recovery_and_review() -> None:
    draft = json.loads(proposal("The pilot ended in 2025.", END))
    draft["missing_evidence"] = "pilot end year"
    review = json.loads(reviewed((START, 1, START), (END, 2, END)))
    review["gaps"] = ["end year"]
    with exchange([[START, END], [END], [END]], [json.dumps(draft), json.dumps(review)], 2) as env:
        answer = env.service.ask(
            env.conversation_id, "When did the pilot start and end, and in what year?"
        )
        assert len(env.embedder.texts) >= 2
        assert "2025" not in answer.text and "year" in answer.text.lower()


@pytest.mark.parametrize("stage", ["draft", "review"])
def test_s114_failed_stage_is_never_resent(stage: str) -> None:
    failure = genai_errors.APIError(503, {"error": {"status": "UNAVAILABLE"}})
    steps: list[str | Exception] = [failure]
    if stage == "review":
        steps.insert(0, proposal(END, END))
    with exchange([[START, END]], steps, len(steps)) as env, pytest.raises(ChatModelError) as error:
        env.service.ask(env.conversation_id, QUESTION)
    assert str(error.value) == INTERRUPTED_MESSAGE


def test_s115_review_timeout_returns_pending_text_without_a_third_attempt() -> None:
    failure = genai_errors.APIError(504, {"error": {"status": "DEADLINE_EXCEEDED"}})
    with exchange([[START, END]], [proposal(END, END), failure], 2) as env:
        answer = env.service.ask(env.conversation_id, QUESTION)
        assert answer.unverified_draft and "July" in answer.unverified_draft
        assert "July" not in answer.text and not answer.citations


def test_s119_empty_search_explains_insufficient_evidence_without_generation() -> None:
    with exchange([[], [], []], [], 0) as env:
        answer = env.service.ask(env.conversation_id, QUESTION)
        assert not answer.citations and not answer.unverified_draft
        assert any(word in answer.text.lower() for word in ("passage", "source", "evidence"))
        assert answer.text not in (INTERRUPTED_MESSAGE, TIMEOUT_MESSAGE)


def test_s120_initial_search_failure_is_an_interruption_without_generation() -> None:
    with (
        exchange([[START]], [], 0) as env,
        patch.object(env.embedder, "generate", side_effect=RuntimeError("search unavailable")),
        pytest.raises(ChatModelError, match="finish checking"),
    ):
        env.service.ask(env.conversation_id, QUESTION)
