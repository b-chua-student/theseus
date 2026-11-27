"""Tests for the verdict value object."""

from domain.assistant.models.value_objects import Finding, Verdict

MAY = Finding("The pilot started in May", 1)


def test_a_relevant_verdict_with_nothing_unresolved_passes() -> None:
    assert Verdict(verified=(MAY,)).passed is True


def test_a_verdict_that_requests_more_evidence_does_not_pass() -> None:
    verdict = Verdict(verified=(MAY,), missing_evidence="when the pilot ended")

    assert verdict.passed is False
    assert verdict.missing_evidence == "when the pilot ended"


def test_a_verdict_with_an_unresolved_claim_does_not_pass() -> None:
    assert Verdict(verified=(MAY,), unresolved=("ended on July 12",)).passed is False


def test_an_off_topic_verdict_does_not_pass() -> None:
    assert Verdict(relevant=False).passed is False


def test_a_verified_manuscript_finding_has_no_library_citation() -> None:
    finding = Finding("The manuscript says July 12", None, "manuscript")

    assert (finding.citation, finding.source) == (None, "manuscript")
