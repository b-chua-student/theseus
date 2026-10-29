from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from domain.conversation.entities import Exchange


@dataclass(frozen=True)
class SourceResponseDTO:
    chunk_id: UUID
    section_id: UUID
    excerpt: str
    score: float

    def to_dict(self) -> dict:
        return {
            "chunk_id": str(self.chunk_id),
            "section_id": str(self.section_id),
            "excerpt": self.excerpt,
            "score": self.score,
        }


@dataclass(frozen=True)
class ExchangeResponseDTO:
    id: UUID
    query: str
    answer: str | None
    sources: tuple[SourceResponseDTO, ...]
    created_at: str

    @classmethod
    def from_domain(cls, exchange: Exchange) -> ExchangeResponseDTO:
        answer = exchange.answer
        return cls(
            id=exchange.id.value,
            query=exchange.query.content,
            answer=answer.content if answer else None,
            sources=tuple(
                SourceResponseDTO(s.chunk_id, s.section_id, s.excerpt, s.score)
                for s in (answer.sources if answer else ())
            ),
            created_at=exchange.created_at.isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "query": self.query,
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "created_at": self.created_at,
        }
