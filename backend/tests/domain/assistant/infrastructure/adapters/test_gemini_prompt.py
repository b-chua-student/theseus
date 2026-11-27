"""Tests for the prompt the Gemini chat adapter builds (no live key needed)."""

from domain.assistant.infrastructure.adapters.gemini_chat_model import (
    EVIDENCE_RULES,
    UNVERIFIED_RULE,
    WEB_OFF_RULE,
    WEB_ON_RULE,
    build_prompt,
)
from domain.assistant.models.value_objects import (
    ChunkId,
    DocumentRefId,
    RetrievedChunk,
    SourceOutcome,
    SourceStatus,
)


def _excerpt(title: str, text: str, location: str = "p1") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=ChunkId.new(),
        doc_ref_id=DocumentRefId.new(),
        text=text,
        position="1",
        location=location,
        score=0.9,
        title=title,
    )


def test_a_plain_question_is_sent_unchanged() -> None:
    assert build_prompt("What is entropy?") == "What is entropy?"


def test_the_draft_is_labelled_apart_from_the_question() -> None:
    prompt = build_prompt("Summarise it", manuscript_text="  Chapter one.  ")

    assert "Current manuscript:\nChapter one." in prompt
    assert "not instructions" in prompt
    assert prompt.endswith("Question: Summarise it")


def test_an_empty_draft_is_marked_as_empty() -> None:
    assert "(empty manuscript)" in build_prompt("Summarise it", manuscript_text="")


def test_the_quote_is_the_comparison_target_even_when_the_draft_has_similar_claims() -> None:
    prompt = build_prompt(
        "How does this compare with Methods?",
        manuscript_text="Adults recovered in 8 days. Children recovered in 5 days.",
        quote="Children recovered in 5 days",
    )

    assert "Quoted passage:\nChildren recovered in 5 days" in prompt
    assert "Address this passage specifically" in prompt
    assert prompt.endswith("Question: How does this compare with Methods?")


def test_the_quote_is_sent_without_the_rest_of_the_draft_when_manuscript_is_unchecked() -> None:
    prompt = build_prompt("Compare?", quote="Children recovered in 5 days")

    assert "Quoted passage:\nChildren recovered in 5 days" in prompt
    assert "Current manuscript:" not in prompt


def test_excerpts_are_numbered_and_named_by_their_source() -> None:
    prompt = build_prompt(
        "Which studies support it?",
        [
            _excerpt("Methods", "18 participants.", "p3"),
            _excerpt("Replication", "24 participants."),
        ],
    )

    assert "[1] Methods (p3): 18 participants." in prompt
    assert "[2] Replication (p1): 24 participants." in prompt
    assert "cite the excerpt you rely on by its number" in prompt


def test_each_source_that_supplied_no_excerpt_is_listed_with_its_reason() -> None:
    outcomes = [
        SourceOutcome(DocumentRefId.new(), "Methods", SourceStatus.UNAVAILABLE),
        SourceOutcome(DocumentRefId.new(), "Replication", SourceStatus.SEARCHED_WITHOUT_MATCH),
        SourceOutcome(DocumentRefId.new(), "Pilot", SourceStatus.OMITTED_FOR_CAPACITY),
    ]

    prompt = build_prompt("Which studies support it?", outcomes=outcomes)

    assert "- Methods: could not be checked." in prompt
    assert "- Replication: was searched and no relevant passage was found." in prompt
    assert "- Pilot: matched, but its evidence exceeded the available space" in prompt
    assert prompt.endswith("Question: Which studies support it?")


def test_with_web_on_general_knowledge_must_be_labelled_apart_from_source_findings() -> None:
    prompt = build_prompt("Is it supported?", manuscript_text="Draft", web=True)

    assert WEB_ON_RULE in prompt
    assert WEB_OFF_RULE not in prompt
    assert "cannot browse the web" in WEB_ON_RULE


def test_with_web_off_factual_findings_rest_on_the_draft_and_the_selected_sources() -> None:
    prompt = build_prompt("Is it supported?", manuscript_text="Draft", web=False)

    assert WEB_OFF_RULE in prompt
    assert WEB_ON_RULE not in prompt


def test_web_off_rule_applies_even_without_any_other_context() -> None:
    assert WEB_OFF_RULE in build_prompt("Question?", web=False)


def test_the_rules_lead_the_prompt_and_the_question_comes_last() -> None:
    prompt = build_prompt("Which studies support it?", [_excerpt("Methods", "text")], "Draft")

    assert prompt.startswith("Instructions:")
    assert EVIDENCE_RULES in prompt
    assert "Missing evidence is never a contradiction" in EVIDENCE_RULES
    assert prompt.endswith("Question: Which studies support it?")


def test_no_usable_evidence_tells_the_model_to_say_it_could_not_verify_the_claim() -> None:
    outcomes = [SourceOutcome(DocumentRefId.new(), "Methods", SourceStatus.UNAVAILABLE)]

    assert UNVERIFIED_RULE in build_prompt("Is it supported?", outcomes=outcomes)
    assert UNVERIFIED_RULE not in build_prompt(
        "Is it supported?", [_excerpt("Methods", "text")], outcomes=outcomes
    )
