from dataclasses import dataclass
from datetime import datetime

from .value_objects import Answer, ExchangeId, Query


@dataclass(frozen=True, slots=True)
class Exchange:
    """One question and its answer, if recorded yet."""

    id: ExchangeId
    query: Query
    created_at: datetime
    answer: Answer | None = None

    @property
    def is_answered(self) -> bool:
        return self.answer is not None
