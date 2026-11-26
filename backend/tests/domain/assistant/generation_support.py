"""Request-wide acceptance tests for S-014 to S-017 using an offline Gemini SDK spy."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from domain.assistant.infrastructure.adapters.gemini_answer_validator import GeminiAnswerValidator
from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.models.value_objects import ProjectId
from domain.assistant.services.chat import ChatService
from tests.domain.assistant.validation_support import (
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


@dataclass
class BudgetExchange:
    service: ChatService
    conversation_id: str
    project_id: str
    embedder: RecordingEmbedder
    provider: CountingGenerationProvider
    document_id: str


@contextmanager
def exchange(
    searches: list[list[str]],
    response: str | Exception | list[str | Exception],
    expected_calls: int,
) -> Iterator[BudgetExchange]:
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
        yield BudgetExchange(
            service,
            str(service.start(str(project.value)).value),
            str(project.value),
            embedder,
            provider,
            str(document.doc_ref_id.value),
        )
        assert provider.calls == expected_calls, "generation attempts across the whole exchange"


def reviewed(*claims: tuple[str, int, str]) -> str:
    """A relevant review with corrected claims and their supporting passages."""
    return json.dumps(
        {
            "relevant": True,
            "claims": [
                {"text": text, "citation": key, "excerpt": excerpt, "supported": True}
                for text, key, excerpt in claims
            ],
        }
    )


def reviewed_months() -> list[str | Exception]:
    return [proposal(END, END), reviewed((START, 1, START), (END, 2, END))]


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
