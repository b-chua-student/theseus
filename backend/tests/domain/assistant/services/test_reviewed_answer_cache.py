"""Exercise reviewed-answer reuse through normal chat requests with offline adapters."""

import json
from unittest.mock import patch

import pytest

from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.models.errors import ChatModelError
from tests.domain.assistant.generation_support import (
    END,
    START,
    exchange,
    proposal,
    reviewed,
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


def test_replay_recovery_before_cache_hit_and_refresh_changed_evidence() -> None:
    august = "The pilot ended in August."
    draft = json.loads(proposal(END, END))
    draft["missing_evidence"] = "pilot end date"
    responses: list[str | Exception] = [
        json.dumps(draft),
        reviewed((START, 1, START), (END, 2, END)),
        proposal(august, august),
        reviewed((START, 1, START), (august, 2, august)),
    ]
    with exchange([[START], [END], [START], [END], [START], [august]], responses, 4) as env:
        first = env.service.ask(env.conversation_id, QUESTION)
        assert "July" in first.text
        assert env.service.ask(env.conversation_id, QUESTION) == first
        assert env.provider.calls == 2
        latest = env.service.ask(env.conversation_id, QUESTION)
        assert "August" in latest.text and "July" not in latest.text
        assert len(env.embedder.texts) == 6


def test_failed_exchange_save_cannot_publish_a_cache_entry() -> None:
    with exchange([[START, END], [START, END]], reviewed_months() * 2, 4) as env:
        with (
            patch.object(
                InMemoryConversationRepository, "save", side_effect=RuntimeError("save failed")
            ),
            pytest.raises(RuntimeError, match="save failed"),
        ):
            env.service.ask(env.conversation_id, QUESTION)
        assert env.provider.calls == 2
        assert env.service.ask(env.conversation_id, QUESTION).citations
