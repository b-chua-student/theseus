from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from domain.shared.clock import now

from .errors import ExchangeAlreadyAnsweredError
from .value_objects import Answer, ExchangeId, Query


@dataclass(eq=False)
class Exchange:
    """A single query and its answer within a conversation.

    The answer is None until the exchange is responded to, and can be set only once.
    """

    id: ExchangeId
    query: Query
    answer: Answer | None = None
    asked_at: datetime = field(default_factory=now)

    @classmethod
    def open(cls, query: Query) -> Exchange:
        """Open an unanswered exchange for ``query``."""
        return cls(id=ExchangeId.new(), query=query)

    @property
    def is_answered(self) -> bool:
        """Return True if an answer has been recorded."""
        return self.answer is not None

    def respond(self, answer: Answer) -> None:
        """Record ``answer``.

        Raises:
            ExchangeAlreadyAnsweredError: If the exchange already has an answer.
        """
        if self.is_answered:
            raise ExchangeAlreadyAnsweredError(str(self.id.value))
        self.answer = answer
