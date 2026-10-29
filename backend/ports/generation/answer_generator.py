from abc import ABC, abstractmethod

from domain.conversation.entities import Exchange
from ports.retrieval.retriever import RetrievedPassage


class AnswerGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        query: str,
        passages: list[RetrievedPassage],
        history: list[Exchange],
    ) -> str:
        """Generate an answer grounded in the passages."""
