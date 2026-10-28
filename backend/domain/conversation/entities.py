from dataclasses import dataclass

from .value_objects import ExchangeId, Query, Answer


@dataclass
class Exchange:
    id: ExchangeId
    query: Query
    answer: Answer | None
    created_at: datetime
