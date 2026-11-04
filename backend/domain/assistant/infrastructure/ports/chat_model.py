from abc import ABC, abstractmethod

from domain.assistant.models.entities import Exchange
from domain.assistant.models.value_objects import Answer, Query, RetrievedChunk


class ChatModel(ABC):
    """Port for a conversational language model that answers queries."""

    @abstractmethod
    def reply(
        self,
        history: list[Exchange],
        query: Query,
        context: list[RetrievedChunk] | None = None,
    ) -> Answer:
        """Answer ``query``; ``context`` holds retrieved source chunks, best first."""
