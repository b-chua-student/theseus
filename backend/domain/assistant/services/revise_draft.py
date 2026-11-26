from dataclasses import replace

from domain.assistant.infrastructure.ports.answer_validator import AnswerValidator
from domain.assistant.models.value_objects import Answer, Evidence, Query, Verdict


class ReviseDraft:
    """Revises a draft against the evidence admitted for it and resolves the new citations."""

    def __init__(self, validator: AnswerValidator) -> None:
        """Configure the validator that writes the revision."""
        self._validator = validator

    def execute(
        self,
        *,
        question: Query,
        answer: Answer,
        verdict: Verdict,
        evidence: Evidence,
        manuscript_text: str = "",
    ) -> Answer:
        """Return the revised draft, citing only passages that ``evidence`` admits.

        The validator sees the passages in key order, so a key in the revision names the same
        passage as it did in the draft.
        """
        revised = self._validator.revise(
            question=question.text,
            answer=answer,
            verdict=verdict,
            passages=list(evidence.passages),
            manuscript_text=manuscript_text,
        )
        return replace(revised, citations=evidence.citations_for(revised.text))
