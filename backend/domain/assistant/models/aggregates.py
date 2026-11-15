from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.shared.clock import now

from .entities import Exchange
from .errors import (
    EmptyChunksError,
    ExchangeNotFoundError,
    InvalidIndexTransitionError,
    PendingExchangeError,
)
from .value_objects import (
    Answer,
    Chunk,
    ConversationId,
    DocumentRefId,
    ExchangeId,
    IndexedDocumentId,
    IndexedDocumentTitle,
    IndexStatus,
    ProjectId,
    Query,
)


@dataclass(eq=False)
class IndexedDocument:
    """Aggregate tracking a source document's indexing lifecycle and its chunks.

    Status moves PENDING -> INDEXING -> INDEXED or FAILED; chunks are held only when INDEXED.
    Identity is by ``id``, not by field values.
    """

    id: IndexedDocumentId
    doc_ref_id: DocumentRefId
    title: IndexedDocumentTitle
    project_id: ProjectId
    status: IndexStatus = IndexStatus.PENDING
    chunks: list[Chunk] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        title: IndexedDocumentTitle,
        doc_ref_id: DocumentRefId,
        project_id: ProjectId,
    ) -> IndexedDocument:
        """Create a document in the PENDING state with a fresh id."""
        return cls(
            id=IndexedDocumentId.new(),
            doc_ref_id=doc_ref_id,
            title=title,
            project_id=project_id,
        )

    def start_indexing(self) -> None:
        """Move to INDEXING from PENDING, FAILED or INDEXED (reindex).

        Raises:
            InvalidIndexTransitionError: If the current status does not allow it.
        """
        if self.status not in (IndexStatus.PENDING, IndexStatus.FAILED, IndexStatus.INDEXED):
            raise InvalidIndexTransitionError(self.status, IndexStatus.INDEXING)
        self.status = IndexStatus.INDEXING

    def complete_indexing(self, chunks: list[Chunk]) -> None:
        """Store ``chunks`` (replacing any old ones) and move to INDEXED.

        Raises:
            InvalidIndexTransitionError: If not currently INDEXING.
            EmptyChunksError: If ``chunks`` is empty.
        """
        if self.status is not IndexStatus.INDEXING:
            raise InvalidIndexTransitionError(self.status, IndexStatus.INDEXED)
        if not chunks:
            raise EmptyChunksError(str(self.id))
        self.chunks = list(chunks)  # replaces old chunks (reindex)
        self.status = IndexStatus.INDEXED

    def fail_indexing(self) -> None:
        """Discard chunks and move to FAILED.

        Raises:
            InvalidIndexTransitionError: If not currently INDEXING.
        """
        if self.status is not IndexStatus.INDEXING:
            raise InvalidIndexTransitionError(self.status, IndexStatus.FAILED)
        self.chunks.clear()
        self.status = IndexStatus.FAILED

    def mark_stale(self) -> None:
        """Source document changed; needs reindex."""
        self.status = IndexStatus.PENDING

    @property
    def is_searchable(self) -> bool:
        """Return True if the document is fully indexed and can be queried."""
        return self.status is IndexStatus.INDEXED

    def rename(self, title: IndexedDocumentTitle) -> None:
        """Replace the document's title."""
        self.title = title

    def __eq__(self, other: object) -> bool:
        return isinstance(other, IndexedDocument) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(eq=False)
class Conversation:
    """Aggregate for a project's chat, holding an ordered list of exchanges.

    At most one exchange may be unanswered (pending) at a time. Identity is by ``id``.
    """

    id: ConversationId
    project_id: ProjectId
    exchanges: list[Exchange] = field(default_factory=list)
    started_at: datetime = field(default_factory=now)

    @classmethod
    def start(cls, project_id: ProjectId) -> Conversation:
        """Start an empty conversation for ``project_id``."""
        return cls(id=ConversationId.new(), project_id=project_id)

    @property
    def pending(self) -> Exchange | None:
        """Return the trailing unanswered exchange, or None if there is none."""
        last = self.exchanges[-1] if self.exchanges else None
        return last if last and not last.is_answered else None

    @property
    def history(self) -> list[Exchange]:
        """Return the answered exchanges in chronological order."""
        return [e for e in self.exchanges if e.is_answered]

    def ask(self, query: Query) -> Exchange:
        """Open a new exchange for ``query`` and return it.

        Raises:
            PendingExchangeError: If the previous exchange is still unanswered.
        """
        if self.pending is not None:
            raise PendingExchangeError("Previous query is still awaiting an answer.")
        exchange = Exchange.open(query)
        self.exchanges.append(exchange)
        return exchange

    def discard_pending(self) -> None:
        """Drop an unanswered exchange (e.g. the AI failed) so the user can ask again."""
        if self.pending is not None:
            self.exchanges.pop()

    def answer(self, exchange_id: ExchangeId, answer: Answer) -> None:
        """Record ``answer`` on the exchange identified by ``exchange_id``.

        Raises:
            ExchangeNotFoundError: If no such exchange exists.
        """
        for exchange in self.exchanges:
            if exchange.id == exchange_id:
                exchange.respond(answer)
                return
        raise ExchangeNotFoundError(str(exchange_id.value))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Conversation) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
