from dataclasses import replace

from domain.assistant.infrastructure.ports.answer_validator import AnswerValidator
from domain.assistant.models.value_objects import Answer, Evidence, Query, Verdict
from domain.assistant.services.local_evidence import check_evidence


def revise_from_evidence(
    question: Query,
    evidence: Evidence,
    manuscript_text: str = "",
) -> tuple[Answer, Verdict]:
    """Rebuild a candidate from current passages without a generation or validation call."""
    verdict = check_evidence(question.text, evidence, manuscript_text=manuscript_text)
    return render_checked(verdict, evidence), verdict


def render_checked(verdict: Verdict, evidence: Evidence) -> Answer:
    """Render only locally established statements and server-resolved citation keys."""
    lines = []
    for finding in verdict.verified:
        if finding.source == "manuscript":
            lines.append(f"The manuscript states: {finding.claim}")
        else:
            lines.append(f"{finding.claim.rstrip('.')} [{finding.citation}].")
    if verdict.unresolved:
        lines.append("Could not verify: " + "; ".join(verdict.unresolved) + ".")
    text = " ".join(lines) or "I couldn’t verify an answer from the retrieved passages."
    return Answer(text, evidence.citations_for(text))


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
        timeout: float | None = None,
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
            timeout=timeout,
        )
        return replace(revised, citations=evidence.citations_for(revised.text))
