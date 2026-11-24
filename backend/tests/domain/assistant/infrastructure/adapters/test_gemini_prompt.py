"""Tests for the prompt the Gemini chat adapter builds (no live key needed)."""

from domain.assistant.infrastructure.adapters.gemini_chat_model import build_prompt
from domain.assistant.models.value_objects import ChunkId, DocumentRefId, RetrievedChunk


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
