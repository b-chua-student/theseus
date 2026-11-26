from __future__ import annotations

import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Literal
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
    """A chunk returned from a similarity query, ranked by ``score`` (higher = closer)."""

    chunk_id: ChunkId
    doc_ref_id: DocumentRefId
    text: str
    position: str
    location: str
    score: float


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
    """A passage that an answer cites, identified by its key in the answer's evidence."""

    key: int
    chunk_id: ChunkId
    doc_ref_id: DocumentRefId
    location: str


@dataclass(frozen=True)
class Answer:
    """The assistant's reply; text is stripped and must not be blank.

    ``citations`` lists the passages that the text cites inline as ``[1]``, ``[2]``.
    """

    text: str
    citations: tuple[Citation, ...] = ()

    def __post_init__(self) -> None:
        """Strip whitespace and reject empty text."""
        stripped = self.text.strip()
        if not stripped:
            raise EmptyAnswerError("Answer must not be blank.")
        object.__setattr__(self, "text", stripped)


@dataclass(frozen=True)
class ProposedFinding:
    """Untrusted statement paired with a numbered passage and its exact excerpt."""

    text: str
    citation: int
    excerpt: str


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
            citations.append(Citation(key, passage.chunk_id, passage.doc_ref_id, passage.location))
        return tuple(citations)
