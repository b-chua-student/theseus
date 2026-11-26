from abc import ABC, abstractmethod

from domain.assistant.models.value_objects import Answer, RetrievedChunk, Verdict


class AnswerValidator(ABC):
    """Port for checking a draft answer against the passages it cites, and for revising it.

    Passages are numbered from 1 in the order given. Drafts cite them inline as ``[1]``.
    Implementations raise ``ChatModelError`` when the check or revision cannot be completed.
    """

    @abstractmethod
    def check(
        self,
        *,
        question: str,
        answer: Answer,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Verdict:
        """Check relevance, claims and citations of ``answer`` against ``passages``.

        ``manuscript_text`` is the user's manuscript, when the request supplied one, so that
        statements about it can be told apart from what the sources establish. ``timeout`` is
        the number of seconds left for the request; the call should give up within it.
        """

    @abstractmethod
    def revise(
        self,
        *,
        question: str,
        answer: Answer,
        verdict: Verdict,
        passages: list[RetrievedChunk],
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> Answer:
        """Return a replacement for ``answer`` that resolves what ``verdict`` found wrong.

        ``timeout`` is the number of seconds left for the request; the call should give up
        within it.
        """
