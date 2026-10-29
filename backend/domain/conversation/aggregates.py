from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .entities import Exchange
from .value_objects import Answer, ConversationId, ExchangeId, Query


class Conversation:
    """Aggregate root for a manuscript's question-and-answer conversation.

    Exchanges are kept in the order they were asked. At most one exchange
    can be unanswered at a time, and it is always the last one.
    """

    def __init__(
        self,
        conversation_id: ConversationId,
        manuscript_id: UUID,
    ) -> None:
        self._id = conversation_id
        self._manuscript_id = manuscript_id
        self._exchanges: list[Exchange] = []

    @classmethod
    def create(cls, manuscript_id: UUID) -> Conversation:
        """Create an empty conversation with a new id."""
        return cls(ConversationId(uuid4()), manuscript_id)

    @property
    def conversation_id(self) -> ConversationId:
        return self._id

    @property
    def manuscript_id(self) -> UUID:
        return self._manuscript_id

    @property
    def exchanges(self) -> tuple[Exchange, ...]:
        """All exchanges in the order asked."""
        return tuple(self._exchanges)

    def ask(self, content: str) -> Exchange:
        """Record a new question.

        Args:
            content: The question text.

        Returns:
            The new, unanswered exchange.

        Raises:
            ValueError: If the content is empty, or the previous question
                is still unanswered.
        """
        if self._exchanges and not self._exchanges[-1].is_answered:
            raise ValueError("Previous question is still unanswered")

        exchange = Exchange(
            id=ExchangeId(uuid4()),
            query=Query(content.strip()),
            created_at=datetime.now(UTC),
        )
        self._exchanges.append(exchange)
        return exchange

    def record_answer(self, exchange_id: ExchangeId, answer: Answer) -> Exchange:
        """Attach an answer to an unanswered exchange.

        Args:
            exchange_id: Id of the exchange being answered.
            answer: The generated answer.

        Returns:
            The updated exchange.

        Raises:
            ValueError: If the exchange does not exist or is already answered.
        """
        index = self._index_of(exchange_id)

        if self._exchanges[index].is_answered:
            raise ValueError("Exchange already answered")

        updated = replace(self._exchanges[index], answer=answer)
        self._exchanges[index] = updated
        return updated

    def history(self, limit: int) -> list[Exchange]:
        """Return the most recent answered exchanges, oldest first.

        Args:
            limit: Maximum number of exchanges to return.

        Raises:
            ValueError: If the limit is negative.
        """
        if limit < 0:
            raise ValueError("Limit cannot be negative")
        if limit == 0:
            return []

        answered = [e for e in self._exchanges if e.is_answered]
        return answered[-limit:]

    def _index_of(self, exchange_id: ExchangeId) -> int:
        for index, exchange in enumerate(self._exchanges):
            if exchange.id == exchange_id:
                return index
        raise ValueError("Exchange does not exist")
