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
        manuscript_text: str | None = None,
        quote: str | None = None,
    ) -> Answer:
        """Answer ``query`` from the history and the inputs given.

        ``context`` holds the admitted source excerpts, best first. An excerpt is cited by its
        1-based position in that list. ``manuscript_text`` is the current draft, or None when
        Manuscript is not selected. ``quote`` is the exact passage the writer quoted, or None;
        the answer addresses it, and it is kept apart from the question in ``query``.
        """
