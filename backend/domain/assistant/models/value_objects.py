from __future__ import annotations

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Literal, cast
from uuid import UUID, uuid4

from .errors import (
    EmptyAnswerError,
    EmptyQueryError,
    InvalidConversationIdError,
    InvalidDocumentRefIdError,
    InvalidExchangeIdError,
    InvalidIndexedDocumentIdError,
    InvalidProjectIdError,
)


@dataclass(frozen=True)
class IndexedDocumentId:
    """Identity of an IndexedDocument; value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Validate that the ID is a UUID."""
        if not isinstance(self.value, UUID):
            raise InvalidIndexedDocumentIdError("invalid indexed document id")

    @classmethod
    def new(cls) -> IndexedDocumentId:
        """Generate a new random id."""
        return cls(value=uuid4())


@dataclass(frozen=True)
class ProjectId:
    """Identity of a project; value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Validate that the ID is a UUID."""
        if not isinstance(self.value, UUID):
            raise InvalidProjectIdError("invalid project id")

    @classmethod
    def new(cls) -> ProjectId:
        """Generate a new random id."""
        return cls(value=uuid4())

    @classmethod
    def from_str(cls, text: str) -> ProjectId:
        """Parse an id from its string form.

        Raises:
            InvalidProjectIdError: If ``text`` is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidProjectIdError(f"invalid project id '{text}'") from None


@dataclass(frozen=True)
class DocumentRefId:
    """Stable reference to a source document being indexed; value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Validate that the ID is a UUID."""
        if not isinstance(self.value, UUID):
            raise InvalidDocumentRefIdError("invalid document reference id")

    @classmethod
    def new(cls) -> DocumentRefId:
        """Generate a new random id."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> DocumentRefId:
        """Parse an id from its string form.

        Raises:
            InvalidDocumentRefIdError: If ``text`` is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidDocumentRefIdError(f"invalid document reference id '{text}'") from None


@dataclass(frozen=True)
class IndexedDocumentTitle:
    """Human-readable title of an indexed document."""

    value: str


class IndexStatus(Enum):
    """Indexing lifecycle state of an IndexedDocument."""

    PENDING = 0
    INDEXING = 1
    INDEXED = 2
    FAILED = 3


@dataclass(frozen=True)
class ChunkId:
    """Identity of a Chunk; wraps a UUID."""

    value: UUID

    @classmethod
    def new(cls) -> ChunkId:
        """Generate a new random id."""
        return cls(value=uuid4())


@dataclass(eq=False)
class Chunk:
    """A retrievable passage of a document, with its position, location and content hash.

    Identity is by ``id``.
    """

    id: ChunkId
    text: str
    position: str
    location: str
    content_hash: str


@dataclass(frozen=True)
class Embedding:
    """Vector representation of the chunk identified by ``chunk_id``."""

    chunk_id: ChunkId
    vector: list[float]


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned from a similarity query, ranked by ``score`` (higher = closer).

    ``title`` is the title of the source the chunk belongs to. Vector stores leave it blank;
    the chat service fills it in.
    """

    chunk_id: ChunkId
    doc_ref_id: DocumentRefId
    text: str
    position: str
    location: str
    score: float
    title: str = ""


@dataclass(frozen=True)
class ConversationId:
    """Identity of a Conversation; value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Validate that the ID is a UUID."""
        if not isinstance(self.value, UUID):
            raise InvalidConversationIdError("invalid conversation id")

    @classmethod
    def new(cls) -> ConversationId:
        """Generate a new random id."""
        return cls(uuid4())

    @classmethod
    def from_str(cls, text: str) -> ConversationId:
        """Parse an id from its string form.

        Raises:
            InvalidConversationIdError: If ``text`` is not a valid UUID.
        """
        try:
            return cls(UUID(text))
        except (ValueError, AttributeError, TypeError):
            raise InvalidConversationIdError(f"invalid conversation id '{text}'") from None


@dataclass(frozen=True)
class ExchangeId:
    """Identity of an Exchange; value must be a UUID."""

    value: UUID

    def __post_init__(self) -> None:
        """Validate that the ID is a UUID."""
        if not isinstance(self.value, UUID):
            raise InvalidExchangeIdError("invalid exchange id")

    @classmethod
    def new(cls) -> ExchangeId:
        """Generate a new random id."""
        return cls(uuid4())


@dataclass(frozen=True)
class Query:
    """A user's question; text is stripped and must not be blank."""

    text: str

    def __post_init__(self) -> None:
        """Strip whitespace and reject empty text."""
        stripped = self.text.strip()
        if not stripped:
            raise EmptyQueryError("Query must not be blank.")
        object.__setattr__(self, "text", stripped)


@dataclass(frozen=True)
class Citation:
    """A source passage an answer relies on, resolved from the excerpts the model was given.

    ``key`` is the exchange-local number the model cites in square brackets, such as ``[1]``.
    """

    key: int
    chunk_id: ChunkId | None
    doc_ref_id: DocumentRefId
    location: str
    title: str | None = None


class SourceStatus(Enum):
    """Why a selected source supplied no evidence to an exchange."""

    UNAVAILABLE = "unavailable"
    SEARCHED_WITHOUT_MATCH = "searched_without_match"
    OMITTED_FOR_CAPACITY = "omitted_for_capacity"


_STATUS_REASONS = {
    SourceStatus.UNAVAILABLE: "could not be checked.",
    SourceStatus.SEARCHED_WITHOUT_MATCH: "was searched and no relevant passage was found.",
    SourceStatus.OMITTED_FOR_CAPACITY: (
        "matched, but its evidence exceeded the available space and was not supplied."
    ),
}


@dataclass(frozen=True)
class SourceOutcome:
    """What happened to one selected source that supplied no evidence.

    A source that supplied at least one passage has no outcome. ``unavailable`` means it could
    not be searched at send time. ``searched_without_match`` means the search completed and no
    passage met the relevance threshold. ``omitted_for_capacity`` means relevant passages were
    found but none fit in the evidence budget.
    """

    doc_ref_id: DocumentRefId
    title: str
    status: SourceStatus

    def record(self) -> str:
        """Return the one-line, named record of this outcome that the model receives."""
        return f"{self.title}: {_STATUS_REASONS[self.status]}"


@dataclass(frozen=True)
class SelectedSource:
    """A library source the writer had checked, kept with its title as it was then."""

    id: str
    title: str


@dataclass(frozen=True)
class Answer:
    """The assistant's reply; text is stripped and must not be blank.

    ``citations`` lists the passages that the text cites inline as ``[1]``, ``[2]``.
    """

    text: str
    citations: tuple[Citation, ...] = ()
    unverified_draft: str | None = None

    def __post_init__(self) -> None:
        """Strip whitespace and reject empty text."""
        stripped = self.text.strip()
        if not stripped:
            raise EmptyAnswerError("Answer must not be blank.")
        object.__setattr__(self, "text", stripped)


ContextScope = Literal["none", "manuscript", "source_library"]
CONTEXT_SCOPES: tuple[ContextScope, ...] = ("none", "manuscript", "source_library")


@dataclass(frozen=True)
class ExchangeContext:
    """Independent manuscript, library and quote inputs for one exchange.

    ``manuscript_text`` is None when Manuscript is not selected. ``search_library`` says whether
    library sources are searched. ``source_ids`` are the requested sources, kept as sent so the
    conversation can remember them; None while searching means every active project source (the
    legacy "all library sources" selection). ``quote`` is the exact passage the writer quoted, or
    None. ``scope`` is the legacy scope the inputs map to. ``web`` says whether Web is checked.
    """

    scope: ContextScope
    manuscript_text: str | None = None
    search_library: bool = False
    source_ids: tuple[str, ...] | None = None
    quote: str | None = None
    web: bool = False

    @property
    def manuscript(self) -> bool:
        """Return whether Manuscript is checked, that is, whether the draft is used."""
        return self.manuscript_text is not None

    @classmethod
    def decode(
        cls,
        context_scope: str,
        manuscript_text: str = "",
        source_ids: list[str] | None = None,
        quote: str | None = None,
        *,
        web: bool | None = None,
        manuscript: bool | None = None,
    ) -> ExchangeContext:
        """Decode a request's legacy scope and fields into independent inputs.

        ``none`` uses neither the draft nor the library. ``manuscript`` uses the draft alone.
        ``source_library`` searches the library and also uses the draft when one is sent, which
        is how a combined request is expressed. A blank quote counts as no quote; any other
        quote is kept exactly as written.

        ``web`` and ``manuscript`` are the writer's checked items. When ``manuscript`` is given,
        the draft is used exactly when it is true. When ``web`` is missing, only legacy ``none``
        meant Web.

        Raises:
            ValueError: If ``context_scope`` is not a supported scope.
        """
        exact_quote = quote if quote is not None and quote.strip() else None
        requested = tuple(source_ids) if source_ids is not None else None
        if context_scope not in CONTEXT_SCOPES:
            raise ValueError("Unsupported assistant context scope")
        if manuscript is not None:
            draft = manuscript_text if manuscript else None
        elif context_scope == "manuscript" or (
            context_scope == "source_library" and manuscript_text.strip()
        ):
            draft = manuscript_text
        else:
            draft = None
        return cls(
            scope=cast("ContextScope", context_scope),
            manuscript_text=draft,
            search_library=context_scope == "source_library",
            source_ids=requested,
            quote=exact_quote,
            web=web if web is not None else context_scope == "none",
        )


@dataclass(frozen=True)
class ProposedFinding:
    """Untrusted statement paired with a numbered passage and its exact excerpt."""

    text: str
    citation: int
    excerpt: str


@dataclass(frozen=True)
class SourceDraft:
    """One generated draft and its evidence needs, pending independent review."""

    answer: Answer
    claims: tuple[ProposedFinding, ...]
    missing_evidence: str | None = None


@dataclass(frozen=True)
class Finding:
    """A claim that was checked and found supported.

    A ``library`` finding carries ``citation``, the 1-based position of the passage in the list
    supplied for the draft. A ``manuscript`` finding is supported by the user's manuscript text
    and has no library citation.
    """

    claim: str
    citation: int | None
    source: Literal["library", "manuscript"] = "library"


@dataclass(frozen=True)
class Verdict:
    """The result of checking one draft answer against its passages.

    ``verified`` holds supported claims, ``unresolved`` the claims that failed, ``gaps`` the gaps
    that the checked passages establish, and ``missing_evidence`` what a new search should look
    for. A draft passes when it is relevant, nothing is unresolved and no further evidence is
    requested.
    """

    relevant: bool = True
    verified: tuple[Finding, ...] = ()
    unresolved: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    missing_evidence: str | None = None

    @property
    def passed(self) -> bool:
        """Whether the draft is relevant, fully supported and needs no further search."""
        return self.relevant and not self.unresolved and self.missing_evidence is None


@dataclass(frozen=True)
class Evidence:
    """The passages admitted for a draft answer.

    A passage's key is its 1-based position. Merging keeps retained passages in place, so the
    keys that a draft already cites stay valid when more evidence is added.
    """

    passages: tuple[RetrievedChunk, ...] = ()

    def merge(
        self,
        found: Sequence[RetrievedChunk],
        limit: int,
        keep: Collection[int] | None = None,
    ) -> Evidence:
        """Add passages not already present, by chunk identity, up to ``limit`` passages.

        When the evidence is full and ``keep`` is given, a passage whose key is not in ``keep``
        gives up its place to a new passage, lowest-ranked first. The new passage takes over
        that key, so every other key still names the same passage. Without ``keep``, nothing
        is given up.
        """
        merged = list(self.passages[:limit])
        known = {passage.chunk_id for passage in merged}
        added: set[int] = set()
        for passage in found:
            if passage.chunk_id in known:
                continue
            if len(merged) < limit:
                merged.append(passage)
                added.add(len(merged))
            elif keep is not None:
                free = [
                    key for key in range(len(merged), 0, -1) if key not in keep and key not in added
                ]
                if not free:
                    break
                known.discard(merged[free[0] - 1].chunk_id)
                merged[free[0] - 1] = passage
                added.add(free[0])
            else:
                break
            known.add(passage.chunk_id)
        return Evidence(tuple(merged))

    def citations_for(self, text: str) -> tuple[Citation, ...]:
        """Resolve the ``[n]`` keys in ``text`` to admitted passages, in order of appearance.

        Keys that name no admitted passage are dropped.
        """
        citations: list[Citation] = []
        seen: set[int] = set()
        for match in re.finditer(r"\[(\d+)\]", text):
            key = int(match.group(1))
            if key in seen or not 1 <= key <= len(self.passages):
                continue
            seen.add(key)
            passage = self.passages[key - 1]
            citations.append(
                Citation(
                    key,
                    passage.chunk_id,
                    passage.doc_ref_id,
                    passage.location,
                    passage.title or None,
                )
            )
        return tuple(citations)
