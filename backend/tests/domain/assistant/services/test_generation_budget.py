"""Request-wide acceptance tests for S-014 to S-017 using an offline Gemini SDK spy."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from google.genai import errors as genai_errors

from domain.assistant.infrastructure.adapters.gemini_answer_validator import GeminiAnswerValidator
from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.models.errors import ChatModelError
from domain.assistant.models.value_objects import ProjectId
from domain.assistant.services.chat import ChatService
from tests.domain.assistant.validation_support import (
    INTERRUPTED_MESSAGE,
    QUESTION,
    TIMEOUT_MESSAGE,
    CountingGenerationProvider,
    FakeClock,
    QueryStep,
    RecordingEmbedder,
    ScriptedVectorStore,
    passage,
    searchable_document,
)

START = "The pilot started in May."
END = "The pilot ended in July."
FOLLOW_UP = "Follow-up ended in August."


@contextmanager
def exchange(
    searches: list[list[str]], response: str | Exception, expected_calls: int
) -> Iterator[tuple[ChatService, str, RecordingEmbedder]]:
    project = ProjectId.from_str(str(uuid4()))
    document = searchable_document(project)
    documents = InMemoryIndexedDocumentRepository()
    documents.add(document)
    texts = dict.fromkeys(text for search in searches for text in search)
    passages = {
        text: replace(passage(f"P{i}", text), doc_ref_id=document.doc_ref_id)
        for i, text in enumerate(texts, start=1)
    }
    clock = FakeClock()
    store = ScriptedVectorStore(
        [QueryStep([passages[text] for text in search]) for search in searches], clock
    )
    embedder = RecordingEmbedder()
    provider = CountingGenerationProvider(response)
    # Both real adapters share the same SDK spy. Embeddings have their own recorder.
    with patch("google.genai.Client", return_value=SimpleNamespace(models=provider)):
        service = ChatService(
            InMemoryConversationRepository(),
            GeminiChatModel(api_key="offline"),
            validator=GeminiAnswerValidator(api_key="offline"),
            clock=clock.now,
            embedding_generator=embedder,
            vector_store=store,
            document_repository=documents,
            source_ids=lambda _: [document.doc_ref_id],
        )
        try:
            yield service, str(service.start(str(project.value)).value), embedder
        finally:
            assert provider.calls == expected_calls, "generation attempts across the whole exchange"


def proposal(end_claim: str, excerpt: str) -> str:
    """Example provider payload for a draft pairing each finding with its evidence."""
    return json.dumps(
        {
            "answer": f"The pilot started in May [1]. {end_claim} [2].",
            "claims": [
                {"text": START, "citation": 1, "excerpt": START},
                {"text": end_claim, "citation": 2, "excerpt": excerpt},
            ],
        }
    )


def test_s014_direct_months_use_only_retrieval() -> None:
    with exchange([[START, END]], AssertionError("Direct answer called Gemini"), 0) as (
        service,
        conversation,
        embedder,
    ):
        answer = service.ask(conversation, QUESTION)
        assert "May" in answer.text and "July" in answer.text
        assert [c.location for c in answer.citations] == ["P1", "P2"]
        assert embedder.texts == [QUESTION]


def test_s015_assisted_answer_uses_pilot_excerpts_once() -> None:
    response = proposal("The pilot ended in July", END)
    with exchange([[START, END, FOLLOW_UP]], response, 1) as (service, conversation, _):
        answer = service.ask(conversation, QUESTION)
        assert "May" in answer.text and "July" in answer.text
        assert "August" not in answer.text
        assert [c.location for c in answer.citations] == ["P1", "P2"]


def test_s016_retrieval_retry_withholds_unsupported_year_without_regeneration() -> None:
    question = "When did the pilot start and end, and in what year did it end?"
    response = proposal("The pilot ended in 2025", END)
    with exchange([[START, END], [END], [END]], response, 1) as (service, conversation, embedder):
        answer = service.ask(conversation, question)
        assert len(embedder.texts) >= 2
        assert "2025" not in answer.text
        assert "year" in answer.text.lower()
        assert any(
            word in answer.text.lower()
            for word in ("unverified", "verify", "establish", "unknown", "specified")
        )


@pytest.mark.parametrize("status", [503, 504], ids=["failure", "provider-timeout"])
def test_s017_failed_attempt_consumes_allowance(status: int) -> None:
    reason = "UNAVAILABLE" if status == 503 else "DEADLINE_EXCEEDED"
    failure = genai_errors.APIError(status, {"error": {"status": reason}})
    with exchange([[START, END, FOLLOW_UP]], failure, 1) as (service, conversation, _):
        if status == 504:
            assert service.ask(conversation, QUESTION).text == TIMEOUT_MESSAGE
            return
        with pytest.raises(ChatModelError) as raised:
            service.ask(conversation, QUESTION)
        assert str(raised.value) == INTERRUPTED_MESSAGE
