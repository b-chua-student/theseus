"""Test harness for the backend combined-context scenarios (T-001).

The scenarios in ``specs/assistant/combined_context/gherkin.feature`` run through the Flask
test client with in-memory repositories, a scripted vector store and a recording chat model.
They describe behavior that later waves implement, so they assume the contract below. Every
assumption lives in this module, so a later task that settles a name differently only has to
change it here.

Request body of ``POST .../conversations/<id>/exchanges`` (D-001, D-006):
    ``query``, ``quote`` (exact quote or null), ``web`` and ``manuscript`` (booleans),
    ``manuscript_text`` (only when Manuscript is checked), ``source_ids`` (UUIDs) and the
    legacy ``context_scope``.

Response of that route (D-004): ``answer`` plus ``citations``, each with a ``source_id``.

Saved conversation JSON (D-006): ``web``, ``manuscript`` and ``source_ids``.

Indexed sources read endpoint (D-009): ``GET /api/projects/<id>/indexed-sources`` returns
``{"source_ids": [...]}``.

``ChatModel.reply`` keyword inputs (D-004, D-007, D-008): ``history``, ``query`` and ``context``
(admitted excerpts) as today, plus ``manuscript_text``, ``quote``, ``web`` and ``outcomes``.
Each outcome has a ``doc_ref_id`` (or ``source_id``) and a ``status`` of ``unavailable``,
``searched_without_match`` or ``omitted_for_capacity``.

``build_container`` options (D-007): ``relevance_threshold``, ``token_counter`` (an object with
``count(text) -> int``), ``context_window`` and ``response_reserve``. They are passed only by
scenarios that need them.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from bootstrap.app import create_app
from bootstrap.container import Container, build_container
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.ports.chat_model import ChatModel
from domain.assistant.infrastructure.ports.vector_store import VectorStore
from domain.assistant.models.aggregates import IndexedDocument
from domain.assistant.models.value_objects import (
    Answer,
    Chunk,
    ChunkId,
    DocumentRefId,
    Embedding,
    IndexedDocumentTitle,
    RetrievedChunk,
)
from domain.assistant.models.value_objects import ProjectId as AssistantProjectId
from domain.project.infrastructure.adapters.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from domain.project.models.aggregates import Project
from domain.project.models.entities import Member
from domain.project.models.value_objects import DisplayName, Email, MemberId, ProjectName, Role
from domain.src_lib.infrastructure.adapters.in_memory_source_repository import (
    InMemorySourceRepository,
)
from domain.src_lib.models.aggregates import Source
from domain.src_lib.models.value_objects import SourceTitle, TextBody

RELEVANT = 0.9
IRRELEVANT = 0.1
RELEVANCE_THRESHOLD = 0.5

UNAVAILABLE = "unavailable"
NO_MATCH = "searched_without_match"
OMITTED = "omitted_for_capacity"

_POSITIONAL_INPUTS = ("history", "query", "context")


def quoted(text: str) -> list[str]:
    """Return the double-quoted names in a step fragment, in order."""
    return re.findall(r'"([^"]+)"', text)


class SourceUnavailableError(RuntimeError):
    """Raised by the scripted vector store when a search touches an unavailable source."""


@dataclass(frozen=True)
class Passage:
    """A scripted passage with a fixed similarity score."""

    text: str
    score: float


class ScriptedVectorStore(VectorStore):
    """Vector store whose results and failures are set by the scenario.

    Every query is recorded so steps can tell which sources were searched. A query that
    includes an unavailable source fails as a whole, as a real batch query would.
    """

    def __init__(self) -> None:
        """Start with no passages, no failing sources and no recorded queries."""
        self.passages: dict[DocumentRefId, list[Passage]] = {}
        self.unavailable: set[DocumentRefId] = set()
        self.queries: list[set[DocumentRefId]] = []

    def upsert(
        self, doc_ref_id: DocumentRefId, embeddings: list[Embedding], chunks: list[Chunk]
    ) -> None:
        """Ignore indexing writes; scenarios script passages directly."""

    def delete(self, doc_ref_id: DocumentRefId) -> None:
        """Drop the scripted passages for ``doc_ref_id``."""
        self.passages.pop(doc_ref_id, None)

    def query(
        self,
        query_embedding: list[float],
        k: int = 5,
        doc_ref_ids: list[DocumentRefId] | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top ``k`` scripted passages of the requested sources."""
        requested = set(doc_ref_ids) if doc_ref_ids is not None else set(self.passages)
        self.queries.append(requested)
        if requested & self.unavailable:
            raise SourceUnavailableError("a requested source cannot be searched")
        results = [
            RetrievedChunk(
                chunk_id=ChunkId.new(),
                doc_ref_id=ref,
                text=passage.text,
                position=str(index),
                location=f"p{index}",
                score=passage.score,
            )
            for ref in requested
            for index, passage in enumerate(self.passages.get(ref, []), 1)
        ]
        results.sort(key=lambda chunk: chunk.score, reverse=True)
        return results[:k]

    @property
    def searched(self) -> set[DocumentRefId]:
        """Return every source any query asked for."""
        return set().union(*self.queries) if self.queries else set()


@dataclass(frozen=True)
class ModelCall:
    """One recorded ``ChatModel.reply`` call, read through the assumed input names."""

    args: tuple[object, ...]
    kwargs: dict[str, object]

    def value(self, name: str) -> object:
        """Return the input called ``name``, or fail if the call has no such input."""
        if name in self.kwargs:
            return self.kwargs[name]
        if name in _POSITIONAL_INPUTS and _POSITIONAL_INPUTS.index(name) < len(self.args):
            return self.args[_POSITIONAL_INPUTS.index(name)]
        raise AssertionError(f"the model call has no {name!r} input")

    def text(self, name: str) -> str:
        """Return a string input, treating None as empty."""
        value = self.value(name)
        if value is None:
            return ""
        text = getattr(value, "text", value)
        assert isinstance(text, str), f"model input {name!r} is not text: {value!r}"
        return text

    @property
    def draft(self) -> str:
        """Return the manuscript text the model received."""
        return self.text("manuscript_text")

    @property
    def quote(self) -> str:
        """Return the quote the model received."""
        return self.text("quote")

    @property
    def question(self) -> str:
        """Return the question text the model received."""
        return self.text("query")

    @property
    def web(self) -> bool:
        """Return whether the model was told Web is enabled."""
        value = self.value("web")
        assert isinstance(value, bool), f"model input 'web' is not a boolean: {value!r}"
        return value

    @property
    def excerpts(self) -> list[tuple[DocumentRefId, str]]:
        """Return the admitted excerpts as (source, text) pairs."""
        value = self.value("context")
        if value is None:
            return []
        assert isinstance(value, list), f"model input 'context' is not a list: {value!r}"
        pairs = []
        for excerpt in value:
            ref: object = getattr(excerpt, "doc_ref_id", None)
            text: object = getattr(excerpt, "text", None)
            assert isinstance(ref, DocumentRefId), f"excerpt has no source: {excerpt!r}"
            assert isinstance(text, str), f"excerpt has no text: {excerpt!r}"
            pairs.append((ref, text))
        return pairs

    @property
    def outcomes(self) -> dict[DocumentRefId, str]:
        """Return the per-source outcome records the model received."""
        value = self.value("outcomes")
        assert isinstance(value, list | tuple), f"model input 'outcomes' is not a list: {value!r}"
        records: dict[DocumentRefId, str] = {}
        for record in value:
            ref: object = getattr(record, "doc_ref_id", None)
            if ref is None:
                source_id: object = getattr(record, "source_id", None)
                ref = DocumentRefId(UUID(str(source_id))) if source_id is not None else None
            status: object = getattr(record, "status", None)
            if isinstance(status, Enum):
                status = status.value
            assert isinstance(ref, DocumentRefId), f"outcome has no source: {record!r}"
            assert isinstance(status, str), f"outcome has no status: {record!r}"
            records[ref] = status
        return records


class RecordingChatModel(ChatModel):
    """Chat model that records every input and returns a fixed answer."""

    def __init__(self) -> None:
        """Start with no recorded calls."""
        self.calls: list[ModelCall] = []

    def reply(self, *args: object, **kwargs: object) -> Answer:
        """Record the call and return a fixed answer."""
        self.calls.append(ModelCall(args, kwargs))
        return Answer("Recorded answer.")

    @property
    def last(self) -> ModelCall:
        """Return the most recent call."""
        assert self.calls, "the model was not called"
        return self.calls[-1]


@dataclass
class FakeTokenCounter:
    """Token counter that charges a fixed cost for each registered snippet in the text."""

    costs: dict[str, int] = field(default_factory=dict)

    def count(self, text: str) -> int:
        """Return the summed cost of every registered snippet occurrence."""
        return sum(cost * text.count(snippet) for snippet, cost in self.costs.items())


@dataclass
class Exchange:
    """The request and response of one exchange."""

    body: dict[str, object]
    response: TestResponse

    @property
    def json(self) -> dict[str, object]:
        """Return the response body."""
        data = self.response.get_json(silent=True)
        assert isinstance(data, dict), f"response is not a JSON object: {self.response.data!r}"
        return data


class CombinedContextHarness:
    """One writer, one project and one conversation, driven through the HTTP API."""

    def __init__(self) -> None:
        """Create the project, its owner and empty repositories."""
        self.owner_id = MemberId.new()
        owner = Member(
            id=self.owner_id,
            display_name=DisplayName("Writer"),
            email=Email("writer@example.com"),
            role=Role.EDITOR,
        )
        self.project = Project.create(name=ProjectName("Combined context"), owner=owner)
        self.project_id = self.project.id.value
        self.projects = InMemoryProjectRepository()
        self.projects.add_project(self.project)
        self.sources = InMemorySourceRepository()
        self.documents = InMemoryIndexedDocumentRepository()
        self.vectors = ScriptedVectorStore()
        self.model = RecordingChatModel()
        self.tokens = FakeTokenCounter()
        self.options: dict[str, object] = {}
        self.ids: dict[str, DocumentRefId] = {}
        self.draft = "My manuscript makes a claim."
        self.web = True
        self.manuscript = False
        self.selected: list[str] = []
        self.extra_ids: list[str] = []
        self.quote: str | None = None
        self.exchanges: list[Exchange] = []
        self._client: FlaskClient | None = None
        self._conversation_id: str | None = None

    # ---- library ----
    def add_source(self, title: str, *, project_id: UUID | None = None) -> DocumentRefId:
        """Add an indexed text source with one default relevant passage."""
        owner_project = project_id or self.project_id
        source = Source.add_text(
            title=SourceTitle(title), content=TextBody(f"{title} text."), project_id=owner_project
        )
        self.sources.save(source)
        ref = DocumentRefId(source.id.value)
        document = IndexedDocument.create(
            IndexedDocumentTitle(title), ref, AssistantProjectId(owner_project)
        )
        document.start_indexing()
        document.complete_indexing(
            [
                Chunk(
                    id=ChunkId.new(),
                    text=f"{title} text.",
                    position="1",
                    location="p1",
                    content_hash=title,
                )
            ]
        )
        self.documents.add(document)
        self.vectors.passages[ref] = [Passage(f"{title} reports a relevant finding.", RELEVANT)]
        if project_id is None:
            self.ids[title] = ref
        return ref

    def set_passages(self, title: str, *passages: Passage) -> None:
        """Replace the scripted passages of a source."""
        self.vectors.passages[self.ids[title]] = list(passages)

    def make_unavailable(self, title: str) -> None:
        """Make every search that touches the source fail."""
        self.vectors.unavailable.add(self.ids[title])

    def no_match(self, title: str) -> None:
        """Give the source only below-threshold passages, with the threshold configured."""
        self.set_passages(title, Passage(f"{title} discusses something unrelated.", IRRELEVANT))
        self.options["relevance_threshold"] = RELEVANCE_THRESHOLD

    def configure_budget(self, *, window: int, reserve: int = 0) -> None:
        """Pass the scripted token counter and context window to the container."""
        self.options.update(
            token_counter=self.tokens, context_window=window, response_reserve=reserve
        )

    def ref(self, title: str) -> DocumentRefId:
        """Return the library entry ID of a source in this project."""
        return self.ids[title]

    def titles(self, refs: set[DocumentRefId]) -> set[str]:
        """Return the titles of the given sources (unknown IDs as strings)."""
        names = {ref: title for title, ref in self.ids.items()}
        return {names.get(ref, str(ref.value)) for ref in refs}

    # ---- selection ----
    def check_only(self, names: list[str]) -> None:
        """Make exactly ``names`` checked; Web is checked only if listed."""
        self.web = "Web" in names
        self.manuscript = "Manuscript" in names
        self.selected = [name for name in names if name not in ("Web", "Manuscript")]

    def select(self, names: list[str], *, web_off: bool = False) -> None:
        """Check ``names``; Web keeps its state unless it is turned off."""
        self.manuscript = "Manuscript" in names
        self.selected = [name for name in names if name not in ("Web", "Manuscript")]
        if web_off:
            self.web = False

    def quote_from_editor(self, text: str) -> None:
        """Quote a passage of the draft, adding it to the draft if needed."""
        if text not in self.draft:
            self.draft = f"{self.draft} {text}."
        self.quote = text

    def choose_all_indexed(self) -> None:
        """Copy the project's indexed source IDs from the read endpoint."""
        response = self.client.get(f"/api/projects/{self.project_id}/indexed-sources")
        assert response.status_code == 200, (
            f"indexed sources endpoint returned {response.status_code}"
        )
        data = response.get_json()
        assert isinstance(data, dict) and isinstance(data.get("source_ids"), list)
        names = {str(ref.value): title for title, ref in self.ids.items()}
        self.selected = [names[str(value)] for value in data["source_ids"]]

    # ---- app ----
    @property
    def client(self) -> FlaskClient:
        """Build the app on first use, with any configured container options."""
        if self._client is None:
            factory: Callable[..., Container] = build_container
            container = factory(
                project_repo=self.projects,
                source_repo=self.sources,
                indexed_document_repo=self.documents,
                vector_store=self.vectors,
                chat_model=self.model,
                **self.options,
            )
            app = create_app({"TESTING": True}, container=container)
            self._client = app.test_client()
            with self._client.session_transaction() as session:
                session["user_id"] = str(self.owner_id.value)
        return self._client

    @property
    def conversation_id(self) -> str:
        """Start the conversation on first use and return its ID."""
        if self._conversation_id is None:
            response = self.client.post(f"/api/projects/{self.project_id}/conversations")
            assert response.status_code == 201, response.data
            data = response.get_json()
            assert isinstance(data, dict) and isinstance(data.get("id"), str)
            self._conversation_id = data["id"]
        return self._conversation_id

    def request_body(self, question: str) -> dict[str, object]:
        """Return the exchange request for the current selection."""
        source_ids = [str(self.ref(name).value) for name in self.selected] + self.extra_ids
        if self.web and not self.manuscript and not source_ids:
            scope = "none"
        elif not source_ids:
            scope = "manuscript"
        else:
            scope = "source_library"
        return {
            "query": question,
            "quote": self.quote,
            "web": self.web,
            "manuscript": self.manuscript,
            "manuscript_text": self.draft if self.manuscript else "",
            "source_ids": source_ids if scope != "none" else None,
            "context_scope": scope,
        }

    def ask(self, question: str) -> Exchange:
        """Send a question with the current selection and record the exchange."""
        body = self.request_body(question)
        path = f"/api/projects/{self.project_id}/conversations/{self.conversation_id}/exchanges"
        exchange = Exchange(body, self.client.post(path, json=body))
        self.exchanges.append(exchange)
        assert exchange.response.status_code == 201, (
            f"exchange returned {exchange.response.status_code}: {exchange.response.data!r}"
        )
        return exchange

    @property
    def last(self) -> Exchange:
        """Return the most recent exchange."""
        assert self.exchanges, "no question was asked"
        return self.exchanges[-1]

    def saved_conversation(self) -> dict[str, object]:
        """Return the saved conversation JSON."""
        response = self.client.get(
            f"/api/projects/{self.project_id}/conversations/{self.conversation_id}"
        )
        assert response.status_code == 200, response.data
        data = response.get_json()
        assert isinstance(data, dict)
        return data

    def cited_sources(self) -> set[str]:
        """Return the source IDs cited in the last response."""
        citations = self.last.json.get("citations")
        assert isinstance(citations, list), "the response has no 'citations' list"
        ids = set()
        for citation in citations:
            assert isinstance(citation, dict) and isinstance(citation.get("source_id"), str)
            ids.add(citation["source_id"])
        return ids
