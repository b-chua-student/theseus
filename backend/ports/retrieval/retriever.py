from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RetrievedPassage:
    chunk_id: UUID
    section_id: UUID
    text: str
    score: float


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, manuscript_id: UUID, query: str, limit: int) -> list[RetrievedPassage]:
        """Return the most relevant passages for a manuscript, best first."""
