from __future__ import annotations

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
class Answer:
    """The assistant's reply; text is stripped and must not be blank."""

    text: str

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
    None. ``scope`` is the legacy scope the inputs map to.
    """

    scope: ContextScope
    manuscript_text: str | None = None
    search_library: bool = False
    source_ids: tuple[str, ...] | None = None
    quote: str | None = None

    @classmethod
    def decode(
        cls,
        context_scope: str,
        manuscript_text: str = "",
        source_ids: list[str] | None = None,
        quote: str | None = None,
    ) -> ExchangeContext:
        """Decode a request's legacy scope and fields into independent inputs.

        ``none`` uses neither the draft nor the library. ``manuscript`` uses the draft alone.
        ``source_library`` searches the library and also uses the draft when one is sent, which
        is how a combined request is expressed. A blank quote counts as no quote; any other
        quote is kept exactly as written.

        Raises:
            ValueError: If ``context_scope`` is not a supported scope.
        """
        exact_quote = quote if quote is not None and quote.strip() else None
        requested = tuple(source_ids) if source_ids is not None else None
        if context_scope == "none":
            return cls(scope="none", source_ids=requested, quote=exact_quote)
        if context_scope == "manuscript":
            return cls(
                scope="manuscript",
                manuscript_text=manuscript_text,
                source_ids=requested,
                quote=exact_quote,
            )
        if context_scope == "source_library":
            return cls(
                scope="source_library",
                manuscript_text=manuscript_text if manuscript_text.strip() else None,
                search_library=True,
                source_ids=requested,
                quote=exact_quote,
            )
        raise ValueError("Unsupported assistant context scope")
