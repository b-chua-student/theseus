from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConversationId:
    """Identifier of a conversation."""

    value: UUID


@dataclass(frozen=True, slots=True)
class ExchangeId:
    """Identifier of an exchange."""

    value: UUID


@dataclass(frozen=True, slots=True)
class Query:
    """A user's question."""

    content: str

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the content is empty or whitespace only.
        """
        if not self.content.strip():
            raise ValueError("Query cannot be empty")


@dataclass(frozen=True, slots=True)
class PassageReference:
    """Points to a chunk that supported an answer."""

    chunk_id: UUID
    section_id: UUID
    excerpt: str
    score: float


@dataclass(frozen=True, slots=True)
class Answer:
    """A generated answer and the passages that support it."""

    content: str
    sources: tuple[PassageReference, ...] = ()

    def __post_init__(self) -> None:
        """Raises:
        ValueError: If the content is empty or whitespace only.
        """
        if not self.content.strip():
            raise ValueError("Answer cannot be empty")
