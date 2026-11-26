from dataclasses import dataclass

from domain.assistant.infrastructure.ports.answer_validator import AnswerProposer
from domain.assistant.models.errors import AnswerValidationError
from domain.assistant.models.value_objects import Answer, Evidence, Query, Verdict
from domain.assistant.services.answer_validation import INTERRUPTED_MESSAGE
from domain.assistant.services.local_evidence import check_evidence
from domain.assistant.services.revise_draft import render_checked, revise_from_evidence


@dataclass(frozen=True)
class SourceAnswerCandidates:
    """Build candidates for the exchange owner, which manages retries and generation allowance."""

    proposer: AnswerProposer | None

    def local(
        self, question: Query, evidence: Evidence, manuscript_text: str = ""
    ) -> tuple[Answer, Verdict]:
        """Construct or revise an answer locally, including after a retrieval retry."""
        return revise_from_evidence(question, evidence, manuscript_text)

    def assisted(
        self,
        question: Query,
        evidence: Evidence,
        manuscript_text: str = "",
        timeout: float | None = None,
    ) -> tuple[Answer, Verdict]:
        """Request one proposal and locally recheck its excerpts before rendering a candidate."""
        if self.proposer is None:
            raise AnswerValidationError(INTERRUPTED_MESSAGE)
        proposals = self.proposer.propose(question.text, evidence, manuscript_text, timeout)
        verdict = check_evidence(
            question.text, evidence, proposals=proposals, manuscript_text=manuscript_text
        )
        return render_checked(verdict, evidence), verdict
