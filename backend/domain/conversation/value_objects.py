from dataclasses import dataclass
from uuid import UUID
from enum import Enum


class AnswerStatus(Enum):
    PENDING = 0
    ANSWERED = 1


@dataclass
class ConversationId:
    value: UUID


@dataclass
class ExchangeId:
    value: UUID


@dataclass
class Query:
    content: str


@dataclass
class Answer:
    content: str
    status: AnswerStatus
    sources: list[str]  # should be list of passage references
