import pytest
from google.genai import errors as genai_errors

from domain.assistant.models.errors import ChatModelError
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
