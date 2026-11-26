from unittest.mock import patch

import pytest
from google.genai import errors as genai_errors

from domain.assistant.models.errors import ChatModelError, ValidationBudgetExceeded
from tests.domain.assistant.generation_support import END, FOLLOW_UP, START, exchange, proposal
from tests.domain.assistant.validation_support import INTERRUPTED_MESSAGE, QUESTION, TIMEOUT_MESSAGE


def test_s014_direct_months_use_only_retrieval() -> None:
    with exchange([[START, END]], AssertionError("Direct answer called Gemini"), 0) as env:
        answer = env.service.ask(env.conversation_id, QUESTION)
        assert "May" in answer.text and "July" in answer.text
        assert [c.location for c in answer.citations] == ["P1", "P2"]
        assert env.embedder.texts == [QUESTION]


def test_s015_assisted_answer_uses_pilot_excerpts_once() -> None:
    response = proposal("The pilot ended in July", END)
    with exchange([[START, END, FOLLOW_UP]], response, 1) as env:
        answer = env.service.ask(env.conversation_id, QUESTION)
        assert "May" in answer.text and "July" in answer.text
        assert "August" not in answer.text
        assert [c.location for c in answer.citations] == ["P1", "P2"]


def test_s016_retrieval_retry_withholds_unsupported_year_without_regeneration() -> None:
    question = "When did the pilot start and end, and in what year did it end?"
    response = proposal("The pilot ended in 2025", END)
    with exchange([[START, END], [END], [END]], response, 1) as env:
        answer = env.service.ask(env.conversation_id, question)
        assert len(env.embedder.texts) >= 2
        assert "2025" not in answer.text
        assert "year" in answer.text.lower()
        assert any(
            word in answer.text.lower()
            for word in (
                "not verified",
                "unverified",
                "verify",
                "establish",
                "unknown",
                "specified",
            )
        )


@pytest.mark.parametrize("status", [503, 504], ids=["failure", "provider-timeout"])
def test_s017_failed_attempt_consumes_allowance(status: int) -> None:
    reason = "UNAVAILABLE" if status == 503 else "DEADLINE_EXCEEDED"
    failure = genai_errors.APIError(status, {"error": {"status": reason}})
    with exchange([[END, FOLLOW_UP]], failure, 1) as env:
        if status == 504:
            assert env.service.ask(env.conversation_id, QUESTION).text == TIMEOUT_MESSAGE
            return
        with pytest.raises(ChatModelError) as raised:
            env.service.ask(env.conversation_id, QUESTION)
        assert str(raised.value) == INTERRUPTED_MESSAGE


@pytest.mark.parametrize("verified_start", [False, True], ids=["s018-pending", "s008-partial"])
def test_deadline_after_generation_uses_one_attempt(verified_start: bool) -> None:  # noqa: FBT001
    passages = [START, END, FOLLOW_UP]
    if not verified_start:
        passages.append("Follow-up started in April.")
    with (
        exchange([passages], proposal(END, END), 1) as env,
        patch(
            "domain.assistant.services.source_answer_candidates.check_evidence",
            side_effect=ValidationBudgetExceeded("Deadline before proposal check completed"),
        ),
    ):
        answer = env.service.ask(env.conversation_id, QUESTION)

    draft = getattr(answer, "unverified_draft", None)
    if verified_start:
        assert "May" in answer.text and [c.location for c in answer.citations] == ["P1"]
        assert not draft
    else:
        assert not answer.citations
        assert draft and END in draft
    assert "July" not in answer.text


def test_s019_deadline_during_retry_after_all_proposals_rejected() -> None:
    passages = [START, END, FOLLOW_UP, "Follow-up started in April."]
    # Even the start claim cites the wrong passage in this proposal.
    response = proposal("The pilot ended on July 12.", END).replace(
        '"citation": 1', '"citation": 3'
    )
    with (
        exchange([passages], response, 1) as env,
        patch(
            "domain.assistant.services.evidence_retriever.EvidenceRetriever.find_more",
            side_effect=ValidationBudgetExceeded("Deadline during retry"),
        ) as retry,
    ):
        answer = env.service.ask(env.conversation_id, QUESTION)
    retry.assert_called_once()
    assert answer.text == TIMEOUT_MESSAGE
    assert not answer.citations
    assert not getattr(answer, "unverified_draft", None)
