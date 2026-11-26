"""Adapter tests for the Gemini answer validator, using a fake Gemini client.

Contract assumed here (the adapter does not exist yet):

* ``domain.assistant.infrastructure.adapters.gemini_answer_validator.GeminiAnswerValidator``
  takes an injectable ``client`` (anything with ``models.generate_content``) and a ``model`` name.
* ``check`` asks the model for JSON with ``relevant`` (bool), ``claims`` (a list of ``text``,
  ``citation`` (passage key or null) and ``supported`` (bool)), ``missing_evidence`` (string or
  null) and ``gaps`` (list of strings), and maps it to a verdict. A claim is verified only when the
  model marks it supported and its citation names one of the supplied passages.
* ``revise`` returns the model's replacement text as an ``Answer``.
* Provider failures and unusable responses raise ``ChatModelError`` (rate limits raise
  ``ChatModelRateLimitedError``), so the service can treat them as validation service errors.
"""

import importlib
import json
from types import SimpleNamespace
from typing import Any

import pytest
from google.genai import errors as genai_errors

from domain.assistant.models.errors import (
    ChatModelError,
    ChatModelRateLimitedError,
    ValidationBudgetExceeded,
)
from domain.assistant.models.value_objects import (
    Answer,
    Evidence,
    Finding,
    ProposedFinding,
    Verdict,
)
from tests.domain.assistant.validation_support import QUESTION, passage

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
PASSAGES = [P1, P2]
DRAFT = "The pilot started in May [1] and ended in July [2]."
MANUSCRIPT = "The pilot ended on July 12."


class FakeModels:
    """Stands in for ``client.models`` and records each request."""

    def __init__(self, reply: str | Exception) -> None:
        self._reply = reply
        self.requests: list[dict[str, Any]] = []

    def generate_content(self, **request: Any) -> SimpleNamespace:  # noqa: ANN401
        self.requests.append(request)
        if isinstance(self._reply, Exception):
            raise self._reply
        return SimpleNamespace(text=self._reply)


def validator_with(reply: str | Exception) -> tuple[Any, FakeModels]:
    module = importlib.import_module(
        "domain.assistant.infrastructure.adapters.gemini_answer_validator"
    )
    models = FakeModels(reply)
    return module.GeminiAnswerValidator(client=SimpleNamespace(models=models), model="fake"), models


def verdict_json(
    *,
    relevant: bool = True,
    claims: list[dict[str, Any]] | None = None,
    missing_evidence: str | None = None,
    gaps: list[str] | None = None,
    states_missing_evidence: bool = False,
) -> str:
    return json.dumps(
        {
            "relevant": relevant,
            "claims": claims or [],
            "missing_evidence": missing_evidence,
            "gaps": gaps or [],
            "states_missing_evidence": states_missing_evidence,
        }
    )


def claim(
    text: str, citation: int | None, *, supported: bool = True, source: str = "library"
) -> dict[str, Any]:
    excerpt = MANUSCRIPT if source == "manuscript" else ""
    if source == "library" and citation in (1, 2):
        excerpt = PASSAGES[citation - 1].text
    return {
        "text": text,
        "citation": citation,
        "supported": supported,
        "source": source,
        "excerpt": excerpt,
    }


def prompt_of(models: FakeModels) -> str:
    """All text sent to the model in the only request."""
    [request] = models.requests
    contents = request["contents"]
    if isinstance(contents, str):
        return contents
    parts = []
    for item in contents:
        if isinstance(item, str):
            parts.append(item)
        else:
            parts.extend(part.text for part in item.parts)
    return "\n".join(parts)


def check(validator: Any, *, manuscript_text: str = "", draft: str = DRAFT) -> Verdict:  # noqa: ANN401
    return validator.check(
        question=QUESTION,
        answer=Answer(draft),
        passages=PASSAGES,
        manuscript_text=manuscript_text,
    )


def test_s001_supported_claims_are_verified_with_their_passage_keys() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim("The pilot started in May", 1),
                claim("The pilot ended in July", 2),
            ]
        )
    )

    verdict = check(validator)

    assert verdict.relevant is True
    assert [(f.claim, f.citation) for f in verdict.verified] == [
        ("The pilot started in May", 1),
        ("The pilot ended in July", 2),
    ]
    assert list(verdict.unresolved) == []
    assert verdict.missing_evidence is None


def test_s002_a_draft_about_a_different_question_is_not_relevant() -> None:
    p3_claims = [claim("The pilot was sponsored by the university", 1)]
    validator, _ = validator_with(verdict_json(relevant=False, claims=p3_claims))

    verdict = check(validator, draft="The pilot was sponsored by the university [1].")

    assert verdict.relevant is False


def test_s003_an_unsupported_claim_is_unresolved_and_not_verified() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim("The pilot started in May", 1),
                claim("The pilot ended on July 12", 2, supported=False),
            ]
        )
    )

    verdict = check(validator)

    assert [f.claim for f in verdict.verified] == ["The pilot started in May"]
    assert list(verdict.unresolved) == ["The pilot ended on July 12"]


@pytest.mark.parametrize(
    ("citation", "supported"),
    [
        pytest.param(1, False, id="cited-passage-does-not-support-the-claim"),
        pytest.param(5, True, id="citation-names-no-supplied-passage"),
        pytest.param(0, True, id="citation-key-is-not-a-position"),
        pytest.param(None, True, id="claim-has-no-citation"),
    ],
)
def test_s004_a_claim_with_an_incorrect_citation_is_unresolved(
    citation: int | None, *, supported: bool
) -> None:
    validator, _ = validator_with(
        verdict_json(claims=[claim("The pilot ended in July", citation, supported=supported)])
    )
    draft = "The pilot ended in July" + (f" [{citation}]." if citation is not None else ".")

    verdict = check(validator, draft=draft)

    assert list(verdict.verified) == []
    assert list(verdict.unresolved) == ["The pilot ended in July"]


def test_s005_reports_the_evidence_to_search_for() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[claim("The pilot started in May", 1), claim("The pilot ended", None)],
            missing_evidence="when the pilot ended",
        )
    )

    verdict = check(validator)

    assert verdict.missing_evidence == "when the pilot ended"
    assert [f.claim for f in verdict.verified] == ["The pilot started in May"]


def test_s006_reports_gaps_that_the_checked_passages_establish() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[claim("The pilot started in May", 1)],
            gaps=["The passages do not give an end date"],
        )
    )

    verdict = check(validator)

    assert list(verdict.gaps) == ["The passages do not give an end date"]


def test_s010_a_gap_is_not_invented_when_the_model_reports_none() -> None:
    validator, _ = validator_with(verdict_json(relevant=False))

    verdict = check(validator)

    assert list(verdict.gaps) == []
    assert verdict.missing_evidence is None


def test_s012_check_sends_the_question_draft_numbered_passages_and_manuscript() -> None:
    validator, models = validator_with(verdict_json(claims=[claim("The pilot started in May", 1)]))

    check(validator, manuscript_text=MANUSCRIPT)

    prompt = prompt_of(models)
    assert QUESTION in prompt
    assert DRAFT in prompt
    assert "[1] (P1) The pilot started in May." in prompt
    assert "[2] (P2) The pilot ended in July." in prompt
    assert MANUSCRIPT in prompt
    assert models.requests[0]["model"] == "fake"


def test_an_incomplete_check_of_a_relevant_draft_is_not_approved() -> None:
    validator, _ = validator_with(verdict_json(relevant=True, claims=[]))

    with pytest.raises(ChatModelError):
        check(validator)


def test_a_draft_that_is_not_relevant_needs_no_claims() -> None:
    validator, _ = validator_with(verdict_json(relevant=False, claims=[]))

    assert check(validator).relevant is False


def test_s005_a_verdict_requesting_more_evidence_is_not_an_accepted_answer() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[claim("The pilot started in May", 1)],
            missing_evidence="when the pilot ended",
        )
    )

    verdict = check(validator, draft="The pilot started in May [1].")

    assert verdict.passed is False
    assert verdict.missing_evidence == "when the pilot ended"
    assert [f.claim for f in verdict.verified] == ["The pilot started in May"]
    assert list(verdict.unresolved) == []


MANUSCRIPT_CLAIM = "The manuscript says the pilot ended on July 12"
REPORT_CLAIM = "The report establishes only July"
S012_DRAFT = "The manuscript says July 12; the report establishes only July [2]."


def test_s012_a_manuscript_statement_is_supported_by_the_manuscript_text() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim(MANUSCRIPT_CLAIM, None, source="manuscript"),
                claim(REPORT_CLAIM, 2),
            ]
        )
    )

    verdict = check(validator, manuscript_text=MANUSCRIPT, draft=S012_DRAFT)

    assert [(f.claim, f.citation, f.source) for f in verdict.verified] == [
        (MANUSCRIPT_CLAIM, None, "manuscript"),
        (REPORT_CLAIM, 2, "library"),
    ]
    assert list(verdict.unresolved) == []
    assert verdict.passed is True


def test_s012_a_manuscript_statement_fails_when_no_manuscript_was_supplied() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim(MANUSCRIPT_CLAIM, None, source="manuscript"),
                claim(REPORT_CLAIM, 2),
            ]
        )
    )

    verdict = check(validator, draft=S012_DRAFT)

    assert [f.claim for f in verdict.verified] == [REPORT_CLAIM]
    assert list(verdict.unresolved) == [MANUSCRIPT_CLAIM]


def test_s012_a_report_statement_needs_the_correct_library_citation() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim(MANUSCRIPT_CLAIM, None, source="manuscript"),
                claim(REPORT_CLAIM, 2),
                claim("The report establishes only July", None),
            ]
        )
    )

    verdict = check(validator, manuscript_text=MANUSCRIPT, draft=S012_DRAFT)

    assert [f.claim for f in verdict.verified] == [MANUSCRIPT_CLAIM, REPORT_CLAIM]
    assert [f.citation for f in verdict.verified] == [None, 2]
    assert list(verdict.unresolved) == ["The report establishes only July"]


def test_s012_a_citation_on_a_manuscript_statement_does_not_make_it_a_library_finding() -> None:
    validator, _ = validator_with(
        verdict_json(claims=[claim(MANUSCRIPT_CLAIM, 1, source="manuscript")])
    )

    verdict = check(validator, manuscript_text=MANUSCRIPT, draft=S012_DRAFT)

    [finding] = verdict.verified
    assert (finding.citation, finding.source) == (None, "manuscript")


def test_s012_attributing_the_manuscript_day_to_the_report_fails_validation() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[
                claim("The report says the pilot ended on July 12", 1, supported=False),
                claim("The pilot ended in July", 1),
            ]
        )
    )

    verdict = check(
        validator,
        manuscript_text=MANUSCRIPT,
        draft="The report says the pilot ended on July 12 [1].",
    )

    assert list(verdict.unresolved) == ["The report says the pilot ended on July 12"]
    assert verdict.passed is False


def test_s012_the_check_instruction_separates_manuscript_claims_from_source_findings() -> None:
    validator, models = validator_with(verdict_json(claims=[claim(REPORT_CLAIM, 2)]))

    check(validator, manuscript_text=MANUSCRIPT, draft=S012_DRAFT)

    instruction = models.requests[0]["config"].system_instruction
    assert '"manuscript"' in instruction
    assert '"library"' in instruction


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        pytest.param(
            genai_errors.APIError(429, {"error": {"message": "slow"}}),
            ChatModelRateLimitedError,
            id="rate-limited",
        ),
        pytest.param(
            genai_errors.APIError(500, {"error": {"message": "down"}}),
            ChatModelError,
            id="provider-error",
        ),
        pytest.param(TimeoutError("timed out"), ChatModelError, id="network-error"),
        pytest.param("", ChatModelError, id="empty-response"),
        pytest.param("not json", ChatModelError, id="malformed-json"),
        pytest.param("{}", ChatModelError, id="missing-fields"),
        pytest.param(
            json.dumps({"relevant": "yes", "claims": []}), ChatModelError, id="wrong-types"
        ),
    ],
)
def test_s011_check_failures_raise_chat_model_errors(
    reply: str | Exception, expected: type[Exception]
) -> None:
    validator, _ = validator_with(reply)

    with pytest.raises(expected):
        check(validator)


def revise(validator: Any, verdict: Verdict, *, manuscript_text: str = "") -> Answer:  # noqa: ANN401
    return validator.revise(
        question=QUESTION,
        answer=Answer("The pilot started in May [1] and ended on July 12 [2]."),
        verdict=verdict,
        passages=PASSAGES,
        manuscript_text=manuscript_text,
    )


def test_s003_revise_returns_the_replacement_and_sends_the_failed_claims() -> None:
    validator, models = validator_with("  The pilot started in May [1] and ended in July [2].  ")
    verdict = Verdict(
        verified=(Finding("The pilot started in May", 1),),
        unresolved=("The pilot ended on July 12",),
    )

    revised = revise(validator, verdict)

    assert revised == Answer("The pilot started in May [1] and ended in July [2].")
    prompt = prompt_of(models)
    assert QUESTION in prompt
    assert "ended on July 12 [2]" in prompt
    assert "The pilot ended on July 12" in prompt
    assert "[1] (P1) The pilot started in May." in prompt
    assert "[2] (P2) The pilot ended in July." in prompt


def test_s012_revise_sends_the_manuscript() -> None:
    validator, models = validator_with("The manuscript says July 12; the report gives July only.")

    revise(
        validator,
        Verdict(unresolved=("The report contradicts the manuscript",)),
        manuscript_text=MANUSCRIPT,
    )

    assert MANUSCRIPT in prompt_of(models)


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        pytest.param(
            genai_errors.APIError(429, {"error": {"message": "slow"}}),
            ChatModelRateLimitedError,
            id="rate-limited",
        ),
        pytest.param(
            genai_errors.APIError(503, {"error": {"message": "down"}}),
            ChatModelError,
            id="provider-error",
        ),
        pytest.param("   ", ChatModelError, id="empty-response"),
    ],
)
def test_s011_revise_failures_raise_chat_model_errors(
    reply: str | Exception, expected: type[Exception]
) -> None:
    validator, _ = validator_with(reply)

    with pytest.raises(expected):
        revise(validator, Verdict(unresolved=("a claim",)))


def provider_timeout_ms(models: FakeModels) -> int | None:
    http_options = models.requests[0]["config"].http_options
    return None if http_options is None else http_options.timeout


def test_proposal_returns_untrusted_excerpts_in_one_attempt() -> None:
    validator, models = validator_with(
        json.dumps(
            {"answer": DRAFT, "claims": [{"text": P2.text, "citation": 2, "excerpt": P2.text}]}
        )
    )
    assert validator.draft(QUESTION, Evidence(tuple(PASSAGES)), timeout=12).claims == (
        ProposedFinding(P2.text, 2, P2.text),
    )
    [request] = models.requests
    assert request["config"].http_options.retry_options.attempts == 1
    assert provider_timeout_ms(models) == 12_000


@pytest.mark.parametrize(
    ("timeout", "expected_ms"),
    [
        pytest.param(10.0, 10_000, id="provider-minimum"),
        pytest.param(100.0, 30_000, id="remaining-time-above-the-default"),
        pytest.param(None, None, id="no-deadline-keeps-the-client-default"),
    ],
)
def test_s009_check_limits_the_provider_call_to_the_remaining_time(
    timeout: float | None, expected_ms: int | None
) -> None:
    validator, models = validator_with(verdict_json(claims=[claim("The pilot started in May", 1)]))

    validator.check(
        question=QUESTION,
        answer=Answer(DRAFT),
        passages=PASSAGES,
        manuscript_text="",
        timeout=timeout,
    )

    assert provider_timeout_ms(models) == expected_ms


def test_s009_revise_limits_the_provider_call_to_the_remaining_time() -> None:
    validator, models = validator_with("The pilot started in May [1].")

    validator.revise(
        question=QUESTION,
        answer=Answer(DRAFT),
        verdict=Verdict(unresolved=("a claim",)),
        passages=PASSAGES,
        manuscript_text="",
        timeout=12.0,
    )

    assert provider_timeout_ms(models) == 12_000


def test_s009_insufficient_remaining_time_skips_provider_call() -> None:
    validator, models = validator_with("unused")
    with pytest.raises(ValidationBudgetExceeded):
        validator.check(question=QUESTION, answer=Answer(DRAFT), passages=PASSAGES, timeout=8)
    assert models.requests == []


def test_s009_provider_deadline_exceeded_signals_validation_timeout() -> None:
    validator, _ = validator_with(
        genai_errors.APIError(504, {"error": {"status": "DEADLINE_EXCEEDED"}})
    )
    with pytest.raises(ValidationBudgetExceeded):
        check(validator)


def test_s011_unrelated_invalid_argument_remains_a_provider_error() -> None:
    validator, _ = validator_with(
        genai_errors.APIError(400, {"error": {"status": "INVALID_ARGUMENT"}})
    )
    with pytest.raises(ChatModelError, match="400"):
        check(validator)


def test_s004_a_claim_verified_for_a_passage_the_draft_does_not_cite_is_unresolved() -> None:
    validator, _ = validator_with(verdict_json(claims=[claim("The pilot started in May", 2)]))

    verdict = check(validator, draft="The pilot started in May [1].")

    assert list(verdict.verified) == []
    assert "The pilot started in May" in verdict.unresolved
    assert verdict.passed is False


def test_s004_a_citation_marker_that_no_claim_was_checked_for_is_unresolved() -> None:
    validator, _ = validator_with(verdict_json(claims=[claim("The pilot started in May", 1)]))

    verdict = check(validator, draft="The pilot started in May [1], as the report [2] notes.")

    assert [f.claim for f in verdict.verified] == ["The pilot started in May"]
    assert len(verdict.unresolved) == 1
    assert "[2]" in verdict.unresolved[0]
    assert verdict.passed is False


def test_s004_a_marker_covered_by_an_unsupported_claim_is_not_reported_twice() -> None:
    validator, _ = validator_with(
        verdict_json(claims=[claim("The pilot ended on July 12", 2, supported=False)])
    )

    verdict = check(validator, draft="The pilot ended on July 12 [2].")

    assert list(verdict.unresolved) == ["The pilot ended on July 12"]


def test_s006_a_relevant_draft_that_only_states_missing_evidence_is_a_checked_result() -> None:
    validator, _ = validator_with(
        verdict_json(
            claims=[],
            gaps=["The passages do not give an end date"],
            states_missing_evidence=True,
        )
    )

    verdict = check(validator, draft="The sources do not say when the pilot ended.")

    assert verdict.relevant is True
    assert list(verdict.gaps) == ["The passages do not give an end date"]
    assert list(verdict.unresolved) == []
    assert verdict.passed is True


def test_s006_a_statement_of_missing_evidence_needs_an_established_gap() -> None:
    validator, _ = validator_with(verdict_json(claims=[], states_missing_evidence=True))

    verdict = check(validator, draft="The sources do not say when the pilot ended.")

    assert verdict.passed is False
    assert len(verdict.unresolved) == 1


def test_a_factual_draft_without_checked_claims_is_still_rejected() -> None:
    validator, _ = validator_with(verdict_json(claims=[], states_missing_evidence=False))

    with pytest.raises(ChatModelError):
        check(validator)


def test_s017_review_disables_sdk_resends() -> None:
    validator, models = validator_with(verdict_json(claims=[claim("The pilot started in May.", 1)]))
    check(validator)
    options = models.requests[0]["config"].http_options
    assert options and options.retry_options and options.retry_options.attempts == 1


def test_review_accepts_a_corrected_citation_only_with_its_exact_excerpt() -> None:
    corrected = claim("The pilot ended in July.", 2)
    corrected["original_citation"] = 1
    validator, _ = validator_with(verdict_json(claims=[corrected]))
    verdict = check(validator, draft="The pilot ended in July [1].")
    assert verdict.passed and verdict.verified == (Finding("The pilot ended in July.", 2),)
    corrected["excerpt"] = P1.text
    validator, _ = validator_with(verdict_json(claims=[corrected]))
    rejected = check(validator, draft="The pilot ended in July [1].")
    assert not rejected.verified and not rejected.passed


def test_source_draft_retains_text_and_search_hint() -> None:
    validator, models = validator_with(
        json.dumps(
            {
                "answer": "The pilot started in May [1].",
                "claims": [{"text": "The start was in May.", "citation": 1, "excerpt": P1.text}],
                "missing_evidence": "pilot end date",
            }
        )
    )
    draft = validator.draft(QUESTION, Evidence(tuple(PASSAGES)))
    assert draft.answer.text == "The pilot started in May [1]."
    assert draft.missing_evidence == "pilot end date"
    assert draft.claims == (ProposedFinding("The start was in May.", 1, P1.text),)
    assert len(models.requests) == 1
