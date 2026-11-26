"""Test doubles and the contract assumed by the answer validation tests.

The tests describe how ``ChatService`` is expected to use a validation port. They are written
before the implementation, so the contract is defined here and must be met by the production
port, value objects and service:

* ``ChatService(..., validator=..., clock=...)``. ``clock`` is a monotonic ``() -> float``.
* The validator offers ``check(question, answer, passages, manuscript_text)`` returning a
  verdict, and ``revise(question, answer, verdict, passages, manuscript_text)`` returning a
  replacement ``Answer``. Both are called with those keyword names.
* A verdict has ``relevant``, ``verified`` (claims with the key of their passage),
  ``unresolved`` (claims that failed), ``gaps`` (gaps that checked passages establish) and
  ``missing_evidence`` (what a new search should look for). A draft passes when it is
  relevant and nothing is unresolved.
* Passage keys are 1-based positions in the list of passages admitted for the draft. Drafts cite
  them inline as ``[1]``. ``Answer.citations`` lists the cited passages with ``key`` and
  ``location``.
"""

from dataclasses import dataclass, field
from uuid import uuid4

from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.answer_validator import AnswerValidator
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.embedding_generator import EmbeddingGenerator
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.entities import Exchange
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    ChunkId,
    DocumentRefId,
    Embedding,
    IndexedDocumentTitle,
    ProjectId,
    Query,
    RetrievedChunk,
    Verdict,
)
from domain.assistant.services.chat import ChatService

QUESTION = "When did the pilot start and end?"
START = 100.0
DEADLINE = START + 30.0

TIMEOUT_MESSAGE = "I couldn\u2019t verify an answer within 30 seconds. Please try again."
INTERRUPTED_MESSAGE = "I couldn\u2019t finish checking this answer. Please try again."
OFF_TOPIC_MESSAGE = "I couldn\u2019t produce a verified answer to your question."
PROGRESS_MESSAGE = "Checking the answer against your sources\u2026"


def passage(location: str, text: str) -> RetrievedChunk:
    """Build a retrieved passage whose location names it (``P1``, ``P2``, ``P3``)."""
    return RetrievedChunk(
        chunk_id=ChunkId.new(),
        doc_ref_id=DocumentRefId.new(),
        text=text,
        position="1",
        location=location,
        score=1.0,
    )


class FakeClock:
    """Controllable monotonic clock."""

    def __init__(self, now: float = START) -> None:
        self.value = now

    def now(self) -> float:
        return self.value

    def set(self, value: float) -> None:
        self.value = value


@dataclass
class CheckStep:
    """One scripted validator check: move the clock, then raise or return."""

    verdict: Verdict | None = None
    error: Exception | None = None
    at: float | None = None


@dataclass
class QueryStep:
    """One scripted search: move the clock, then raise or return passages."""

    results: list[RetrievedChunk] = field(default_factory=list)
    error: Exception | None = None
    at: float | None = None


@dataclass(frozen=True)
class CheckCall:
    """Arguments of one ``check`` call."""

    question: str
    text: str
    passages: list[RetrievedChunk]
    manuscript_text: str
    timeout: float | None = None


@dataclass(frozen=True)
class ReviseCall:
    """Arguments of one ``revise`` call."""

    question: str
    text: str
    verdict: Verdict
    passages: list[RetrievedChunk]
    manuscript_text: str
    timeout: float | None = None


class ScriptedChatModel(ChatModel):
    """Chat model that returns scripted drafts and can take time to draft."""

    def __init__(self, drafts: list[str], clock: FakeClock, takes: float = 0.0) -> None:
        self._drafts = list(drafts)
        self._clock = clock
        self._takes = takes
        self.calls: list[tuple[Query, list[RetrievedChunk] | None]] = []

    def reply(
        self,
        history: list[Exchange],
        query: Query,
        context: list[RetrievedChunk] | None = None,
    ) -> Answer:
        self.calls.append((query, context))
        self._clock.set(self._clock.now() + self._takes)
        return Answer(self._drafts.pop(0))


class ScriptedValidator(AnswerValidator):
    """Validator that returns scripted verdicts and revisions and records its calls."""

    def __init__(self, checks: list[CheckStep], revisions: list[str], clock: FakeClock) -> None:
        self._checks = list(checks)
        self._revisions = list(revisions)
        self._clock = clock
        self.checks: list[CheckCall] = []
        self.revisions: list[ReviseCall] = []

    def check(
        self,
        *,
        question: str,
        answer: Answer,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Verdict:
        self.checks.append(
            CheckCall(question, answer.text, list(passages), manuscript_text, timeout)
        )
        step = self._checks.pop(0)
        if step.at is not None:
            self._clock.set(step.at)
        if step.error is not None:
            raise step.error
        assert step.verdict is not None
        return step.verdict

    def revise(
        self,
        *,
        question: str,
        answer: Answer,
        verdict: Verdict,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Answer:
        self.revisions.append(
            ReviseCall(question, answer.text, verdict, list(passages), manuscript_text, timeout)
        )
        return Answer(self._revisions.pop(0))


class ScriptedVectorStore(VectorStore):
    """Vector store that returns scripted search results and records each search."""

    def __init__(self, queries: list[QueryStep], clock: FakeClock) -> None:
        self._queries = list(queries)
        self._clock = clock
        self.searched_documents: list[list[DocumentRefId] | None] = []

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        return None

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        return None

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        self.searched_documents.append(doc_ref_ids)
        step = self._queries.pop(0)
        if step.at is not None:
            self._clock.set(step.at)
        if step.error is not None:
            raise step.error
        return step.results


class RecordingEmbedder(EmbeddingGenerator):
    """Embedder that records the text it embeds, which is the search query."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    def generate(self, chunks: list[Chunk]) -> list[Embedding]:
        self.texts.extend(chunk.text for chunk in chunks)
        return [Embedding(chunk_id=chunk.id, vector=[0.0, 1.0]) for chunk in chunks]


def searchable_document(project_id: ProjectId) -> IndexedDocument:
    """An indexed, searchable document so that the selected source scope is not empty."""
    chunk = Chunk(id=ChunkId.new(), text="x", position="1", location="p1", content_hash="x")
    document = IndexedDocument.create(
        IndexedDocumentTitle("Pilot report"), DocumentRefId.new(), project_id
    )
    document.start_indexing()
    document.complete_indexing([chunk])
    return document


@dataclass
class Env:
    """A chat service wired to scripted fakes, with one open conversation."""

    service: ChatService
    conversation_id: str
    project_id: str
    repository: InMemoryConversationRepository
    clock: FakeClock
    model: ScriptedChatModel
    validator: ScriptedValidator
    store: ScriptedVectorStore
    embedder: RecordingEmbedder


def build(
    *,
    drafts: list[str],
    searches: list[QueryStep],
    checks: list[CheckStep],
    revisions: list[str] | None = None,
    draft_takes: float = 0.0,
) -> Env:
    project_id = str(uuid4())
    clock = FakeClock()
    repository = InMemoryConversationRepository()
    documents = InMemoryIndexedDocumentRepository()
    document = searchable_document(ProjectId.from_str(project_id))
    documents.add(document)
    model = ScriptedChatModel(drafts, clock, takes=draft_takes)
    validator = ScriptedValidator(checks, revisions or [], clock)
    store = ScriptedVectorStore(searches, clock)
    embedder = RecordingEmbedder()
    service = ChatService(
        repository,
        model,
        embedding_generator=embedder,
        vector_store=store,
        document_repository=documents,
        source_ids=lambda _project: [document.doc_ref_id],
        validator=validator,  # type: ignore[call-arg]
        clock=clock.now,
    )
    conversation_id = str(service.start(project_id).value)
    return Env(
        service, conversation_id, project_id, repository, clock, model, validator, store, embedder
    )


class AcceptingValidator(AnswerValidator):
    """Validator that accepts every draft, for tests that are not about validation."""

    def check(
        self,
        *,
        question: str,
        answer: Answer,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Verdict:
        return Verdict()

    def revise(
        self,
        *,
        question: str,
        answer: Answer,
        verdict: Verdict,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Answer:
        return answer
