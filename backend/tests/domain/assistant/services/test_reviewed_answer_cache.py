"""Exercise reviewed-answer reuse through normal chat requests with offline adapters."""

import json

import pytest

from domain.assistant.models.errors import ChatModelError
from tests.domain.assistant.generation_support import (
    END,
    START,
    exchange,
    proposal,
    reviewed_months,
)
from tests.domain.assistant.validation_support import QUESTION


def test_s014_repeat_rechecks_evidence_and_reuses_the_full_answer() -> None:
    with exchange([[START, END], [START, END]], reviewed_months(), 2) as env:
        first = env.service.ask(env.conversation_id, QUESTION)
        assert env.provider.calls == 2
        second = env.service.ask(env.conversation_id, QUESTION)
        assert second == first and len(second.citations) == 2
        assert env.embedder.texts == [QUESTION, QUESTION]


@pytest.mark.parametrize("change", ["question", "selection", "evidence", "context", "conversation"])
def test_s020_changed_inputs_require_a_fresh_review(change: str) -> None:
    second = [START, END, "New evidence."] if change == "evidence" else [START, END]
    with exchange([[START, END], second], reviewed_months() * 2, 4) as env:
        env.service.ask(env.conversation_id, QUESTION)
        assert env.provider.calls == 2
        conversation = env.conversation_id
        if change == "conversation":
            conversation = str(env.service.start(env.project_id).value)
        answer = env.service.ask(
            conversation,
            QUESTION + " Please clarify." if change == "question" else QUESTION,
            source_ids=[env.document_id] if change == "selection" else None,
            manuscript_text="The manuscript gives a different date." if change == "context" else "",
        )
        assert answer.citations


@pytest.mark.parametrize("outcome", ["partial", "error", "timeout"])
def test_s021_only_fully_reviewed_answers_can_be_reused(outcome: str) -> None:
    from google.genai import errors as genai_errors

    review: str | Exception
    if outcome == "partial":
        review = json.dumps(
            {
                "relevant": True,
                "claims": [{"text": START, "citation": 1, "excerpt": START, "supported": True}],
                "gaps": ["end date"],
            }
        )
    else:
        code = 504 if outcome == "timeout" else 503
        review = genai_errors.APIError(code, {"error": {"message": outcome}})
    with exchange(
        [[START, END], [START, END]], [proposal(END, END), review, *reviewed_months()], 4
    ) as env:
        if outcome == "error":
            with pytest.raises(ChatModelError):
                env.service.ask(env.conversation_id, QUESTION)
        else:
            first = env.service.ask(env.conversation_id, QUESTION)
            if outcome == "partial":
                assert "May" in first.text and "July" not in first.text
            else:
                assert first.unverified_draft
        second = env.service.ask(env.conversation_id, QUESTION)
        assert "July" in second.text and second.citations


def test_s022_previously_reviewed_answer_cannot_override_an_empty_search() -> None:
    with exchange([[START, END], [], [], []], reviewed_months(), 2) as env:
        first = env.service.ask(env.conversation_id, QUESTION)
        assert first.citations
        empty = env.service.ask(env.conversation_id, QUESTION)
        assert not empty.citations and "May" not in empty.text and "July" not in empty.text
