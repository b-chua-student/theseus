import logging
import threading
from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor, wait
from dataclasses import dataclass, field, replace
from typing import cast

from domain.assistant.infrastructure.ports.answer_validator import AnswerValidator
from domain.assistant.models.errors import AnswerValidationError, ValidationBudgetExceeded
from domain.assistant.models.value_objects import (
    Answer,
    Evidence,
    Finding,
    ProjectId,
    Query,
    SourceDraft,
    Verdict,
)
from domain.assistant.services.evidence_retriever import EvidenceRetriever
from domain.assistant.services.reviewed_answer_cache import Recovery, evidence_key
from domain.assistant.services.revise_draft import ReviseDraft

logger = logging.getLogger(__name__)

DEADLINE_SECONDS = 30.0
MAX_RETRIES = 2
# Calls that may run at once, counting calls abandoned at a deadline that are still blocked.
MAX_OUTSTANDING_CALLS = 16
TIMEOUT_MESSAGE = "I couldn\u2019t verify an answer within 30 seconds. Please try again."
INTERRUPTED_MESSAGE = "I couldn\u2019t finish checking this answer. Please try again."
OFF_TOPIC_MESSAGE = "I couldn\u2019t produce a verified answer to your question."


class _DeadlineReached(Exception):  # noqa: N818
    """The request's validation time ran out."""


class _ServiceFailure(Exception):  # noqa: N818
    """A service the validation depends on failed before the deadline."""


@dataclass(frozen=True)
class _Outcome[T]:
    """What one call returned or raised, and when, by the request's clock."""

    value: T | None
    error: Exception | None
    at: float


def _same(first: str, second: str) -> bool:
    return first.strip(" .").casefold() == second.strip(" .").casefold()


@dataclass
class _Progress:
    """What the request has established so far, independent of the current draft."""

    answer: Answer
    evidence: Evidence
    findings: dict[str, Finding] = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)
    unresolved: tuple[str, ...] = ()
    missing_evidence: str | None = None
    relevant_drafts: int = 0
    pending_claims: dict[str, str] = field(default_factory=dict)

    def record(self, verdict: Verdict) -> None:
        """Keep what a relevant draft established; an off-topic draft adds nothing.

        Findings accumulate across drafts. Gaps, unresolved claims and the outstanding
        evidence request come from the latest relevant check, so a gap that a later check no
        longer reports counts as resolved. An evidence request is an open question: it does not
        show that the sources lack the answer.
        """
        if not verdict.relevant:
            return
        self.relevant_drafts += 1
        for finding in verdict.verified:
            self.findings[finding.claim] = finding
        # A claim that a later check disputes is no longer a finding. Findings that a later
        # draft simply does not mention stay.
        for claim in verdict.unresolved:
            for known in [k for k in self.findings if _same(k, claim)]:
                del self.findings[known]
        self.gaps = list(verdict.gaps)
        self.unresolved = verdict.unresolved
        self.missing_evidence = verdict.missing_evidence

    def cited_keys(self) -> set[int]:
        """Keys the current draft or a verified finding relies on."""
        keys = {c.key for c in self.evidence.citations_for(self.answer.text)}
        keys.update(
            f.citation for f in self.findings.values() if f.source == "library" and f.citation
        )
        return keys


class ValidateAnswer:
    """Checks a draft before it is shown, revising it and searching again within a budget.

    The request gets ``max_retries`` retries after the first check, shared by revising and
    searching again, and ``deadline_seconds`` in total starting when the draft is ready. Each
    call is bounded by the time left, and a result that arrives after the deadline is ignored.
    Only the answer returned from ``execute`` may be recorded by the caller.
    """

    def __init__(
        self,
        validator: AnswerValidator | None,
        retriever: EvidenceRetriever,
        clock: Callable[[], float],
        deadline_seconds: float = DEADLINE_SECONDS,
        max_retries: int = MAX_RETRIES,
        max_outstanding_calls: int = MAX_OUTSTANDING_CALLS,
    ) -> None:
        """Configure the validator, the evidence retriever, the monotonic clock and budgets.

        A blocking call cannot be cancelled, so one that outlives its deadline keeps running.
        ``max_outstanding_calls`` bounds those calls: when it is reached, new work is rejected.
        """
        self._validator = validator
        self._retriever = retriever
        self._reviser = ReviseDraft(validator) if validator is not None else None
        self._clock = clock
        self._deadline_seconds = deadline_seconds
        self._max_retries = max_retries
        self._slots = threading.BoundedSemaphore(max_outstanding_calls)

    def review_draft(  # noqa: PLR0913
        self,
        question: Query,
        draft: SourceDraft,
        evidence: Evidence,
        project_id: ProjectId,
        source_ids: list[str] | None,
        manuscript_text: str,
        recovery: list[Recovery],
        on_draft_ready: Callable[[], None] | None,
    ) -> tuple[Answer, bool]:
        """Recover evidence and review once; only a complete success is reusable."""
        deadline = self._clock() + self._deadline_seconds
        if on_draft_ready is not None:
            on_draft_ready()
        validator = self._validator
        if validator is None:
            raise AnswerValidationError(INTERRUPTED_MESSAGE)
        progress = _Progress(answer=draft.answer, evidence=evidence)
        for claim in draft.claims:
            if (
                1 <= claim.citation <= len(evidence.passages)
                and claim.excerpt.strip()
                and claim.excerpt in evidence.passages[claim.citation - 1].text
            ):
                progress.pending_claims[claim.text] = claim.text
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            hint = draft.missing_evidence
            if hint and len(recovery) < self._max_retries:
                keep = frozenset(progress.cited_keys())
                progress.evidence = self._call(
                    executor,
                    deadline,
                    lambda _: self._retriever.find_more(
                        project_id, question, evidence, hint, source_ids, keep=keep
                    ),
                )
                recovery.append(Recovery(hint, keep, evidence_key(progress.evidence)))
            verdict = self._call(
                executor,
                deadline,
                lambda remaining: validator.check(
                    question=question.text,
                    answer=draft.answer,
                    passages=list(progress.evidence.passages),
                    manuscript_text=manuscript_text,
                    timeout=remaining,
                ),
            )
            progress.record(verdict)
            progress.pending_claims.clear()
            if self._clock() >= deadline:
                return self._at_deadline(progress), False
            complete = verdict.passed and bool(verdict.verified) and not verdict.gaps
            return self._exhausted(progress), complete
        except _DeadlineReached:
            return self._at_deadline(progress), False
        except _ServiceFailure as exc:
            raise AnswerValidationError(INTERRUPTED_MESSAGE) from exc.__cause__
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def execute(
        self,
        *,
        question: Query,
        draft: Answer,
        evidence: Evidence,
        project_id: ProjectId,
        source_ids: list[str] | None = None,
        manuscript_text: str = "",
    ) -> Answer:
        """Return the answer to show for ``draft``, which has just become ready.

        Raises:
            AnswerValidationError: If a service error stops the check before the deadline.
        """
        deadline = self._clock() + self._deadline_seconds
        progress = _Progress(answer=draft, evidence=evidence)
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            return self._validate(
                executor, deadline, progress, question, project_id, source_ids, manuscript_text
            )
        except _DeadlineReached:
            return self._at_deadline(progress)
        except _ServiceFailure as exc:
            raise AnswerValidationError(INTERRUPTED_MESSAGE) from exc.__cause__
        finally:
            # A blocking call cannot be cancelled; its late result is never read.
            executor.shutdown(wait=False, cancel_futures=True)

    def _validate(  # noqa: PLR0913
        self,
        executor: Executor,
        deadline: float,
        progress: _Progress,
        question: Query,
        project_id: ProjectId,
        source_ids: list[str] | None,
        manuscript_text: str,
    ) -> Answer:
        validator = self._validator
        assert validator is not None
        retries = 0
        while True:
            verdict = self._call(
                executor,
                deadline,
                lambda timeout: validator.check(
                    question=question.text,
                    answer=progress.answer,
                    passages=list(progress.evidence.passages),
                    manuscript_text=manuscript_text,
                    timeout=timeout,
                ),
            )
            progress.record(verdict)
            if verdict.passed:
                return self._with_citations(progress.answer, progress.evidence)
            if retries >= self._max_retries:
                return self._exhausted(progress)
            retries += 1
            self._retry(
                executor,
                deadline,
                progress,
                verdict,
                question,
                project_id,
                source_ids,
                manuscript_text,
            )

    def _retry(  # noqa: PLR0913
        self,
        executor: Executor,
        deadline: float,
        progress: _Progress,
        verdict: Verdict,
        question: Query,
        project_id: ProjectId,
        source_ids: list[str] | None,
        manuscript_text: str,
    ) -> None:
        """Search again when evidence is missing, then revise; one retry in the budget."""
        if verdict.missing_evidence:
            progress.evidence = self._call(
                executor,
                deadline,
                lambda _timeout: self._retriever.find_more(
                    project_id,
                    question,
                    progress.evidence,
                    verdict.missing_evidence,
                    source_ids,
                    keep=progress.cited_keys(),
                ),
            )
        reviser = self._reviser
        assert reviser is not None
        progress.answer = self._call(
            executor,
            deadline,
            lambda timeout: reviser.execute(
                question=question,
                answer=progress.answer,
                verdict=verdict,
                evidence=progress.evidence,
                manuscript_text=manuscript_text,
                timeout=timeout,
            ),
        )

    def _call[T](self, executor: Executor, deadline: float, work: Callable[[float], T]) -> T:
        """Run ``work`` within the time left and apply the deadline rule to its outcome.

        ``work`` receives the seconds left, so an adapter that supports timeouts can give up
        sooner. A result that arrives after the deadline is still ignored.
        """
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise _DeadlineReached

        if not self._slots.acquire(blocking=False):
            raise _ServiceFailure from RuntimeError("Too many validation calls are outstanding.")

        def run() -> _Outcome[T]:
            try:
                value = work(remaining)
            except Exception as exc:
                return _Outcome(None, exc, self._clock())
            else:
                return _Outcome(value, None, self._clock())
            finally:
                # Released when the call really ends, even if its result was abandoned.
                self._slots.release()

        future = executor.submit(run)
        done, _ = wait([future], timeout=remaining)
        if not done:
            raise _DeadlineReached
        outcome = future.result()
        # A result or an error at or after the deadline is the deadline outcome.
        if outcome.at >= deadline or isinstance(outcome.error, ValidationBudgetExceeded):
            raise _DeadlineReached
        if outcome.error is not None:
            logger.error("ValidateAnswer: a service failed", exc_info=outcome.error)
            raise _ServiceFailure from outcome.error
        return cast("T", outcome.value)

    @staticmethod
    def _with_citations(answer: Answer, evidence: Evidence) -> Answer:
        return replace(answer, citations=evidence.citations_for(answer.text))

    def _at_deadline(self, progress: _Progress) -> Answer:
        if not progress.findings:
            pending = " ".join(progress.pending_claims.values()).strip()
            return Answer(TIMEOUT_MESSAGE, unverified_draft=pending or None)
        closing = self._gap_sentence(progress)
        unchecked = [*self._unresolved(progress), *self._open_question(progress)]
        if unchecked:
            closing.append(f"The following could not be checked in time: {'; '.join(unchecked)}.")
        else:
            closing.append("The rest of the answer could not be checked in time.")
        return self._summary(progress, " ".join(closing))

    def _exhausted(self, progress: _Progress) -> Answer:
        if progress.relevant_drafts == 0:
            return Answer(OFF_TOPIC_MESSAGE)
        closing = self._gap_sentence(progress)
        if unresolved := self._unresolved(progress):
            closing.append(f"Not verified against your sources: {'; '.join(unresolved)}.")
        if open_question := self._open_question(progress):
            # An open request is not proof that the sources lack the answer.
            closing.append(f"Still unverified: {'; '.join(open_question)}.")
        return self._summary(progress, " ".join(closing))

    @staticmethod
    def _gap_sentence(progress: _Progress) -> list[str]:
        """The gaps that checked passages establish, which differ from unfinished checking."""
        if not progress.gaps:
            return []
        return [f"The available passages do not establish: {'; '.join(progress.gaps)}."]

    def _unresolved(self, progress: _Progress) -> list[str]:
        """Unresolved claims, minus any item that is already reported as an established gap."""
        return [
            claim
            for claim in progress.unresolved
            if not any(_same(claim, gap) for gap in progress.gaps)
        ]

    def _open_question(self, progress: _Progress) -> list[str]:
        """The outstanding evidence request, unless a gap or unresolved claim already names it."""
        request = progress.missing_evidence
        if not request:
            return []
        reported = [*progress.gaps, *progress.unresolved]
        return [] if any(_same(request, item) for item in reported) else [request]

    def _summary(self, progress: _Progress, closing: str) -> Answer:
        sentences = [self._sentence(f) for f in progress.findings.values()]
        if not sentences:
            sentences = ["I couldn\u2019t verify any claim in the answer against your sources."]
        text = " ".join([*sentences, closing]).strip()
        return self._with_citations(Answer(text), progress.evidence)

    @staticmethod
    def _sentence(finding: Finding) -> str:
        claim = finding.claim.rstrip(". ")
        if finding.source == "manuscript":
            return f"{claim} (from your manuscript)."
        return f"{claim} [{finding.citation}]."
