from uuid import UUID, uuid4

from .value_objects import ConversationId, ExchangeId, Query, Answer, AnswerStatus
from .entities import Exchange
from datetime import datetime, timezone


class InvalidManuscriptId(ValueError):
    def __init__(self, value: object) -> None:
        super().__init__(
            f"Invalid manuscript id: {value!r}. Expected a UUID, "
            "e.g. '123e4567-e89b-12d3-a456-426614174000'."
        )
        self.value = value


class ExchangeNotFound(LookupError):
    def __init__(self, value: object) -> None:
        super().__init__(f"Exchange with ID: {value!r} not found.")
        self.value = value


class AnswerAlreadyRecorded(Exception):
    def __init__(self, value: object) -> None:
        super().__init__(f"Answer already recorded.")
        self.value = value


class Conversation:
    def __init__(self, manuscript_id: UUID) -> None:
        self._id = ConversationId(uuid4())
        self._manuscript_id = manuscript_id
        self.exchanges: list[Exchange] = []

    @classmethod
    def create(cls, manuscript_id: UUID) -> Conversation:
        try:
            UUID(str(manuscript_id))
        except ValueError:
            raise InvalidManuscriptId(manuscript_id)

        return cls(manuscript_id=manuscript_id)

    def ask(self, query: Query) -> Exchange:
        exchange = Exchange(
            id=ExchangeId(uuid4()), query=query, answer=None, created_at=datetime.now(timezone.utc)
        )
        self.exchanges.append(exchange)
        return exchange

    def record_answer(self, exchange_id: ExchangeId, answer: Answer) -> Exchange:
        for exchange in self.exchanges:
            if exchange.id == exchange_id:
                if exchange.answer is not None:
                    raise AnswerAlreadyRecorded(exchange_id)
                exchange.answer = answer
                return exchange
        raise ExchangeNotFound(exchange_id)

    def history(self, limit: int) -> list[Exchange]:
        if limit <= 0:
            return []
        answered = [
            e
            for e in self.exchanges
            if e.answer is not None and e.answer.status == AnswerStatus.ANSWERED
        ]
        return answered[-limit:]
