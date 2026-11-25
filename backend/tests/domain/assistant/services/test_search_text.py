"""Unit tests for the text embedded to search the library (D-003). Offline: no API calls."""

from domain.assistant.services.search_text import (
    DRAFT_EXCERPT_CHARS,
    build_search_text,
    select_draft_excerpt,
)

QUESTION = "Which selected studies support my enrollment figure?"
CLAIM = "The trial enrolled 18 participants."
FILLER = "The weather station recorded the readings each morning."


def long_draft(*, claim_at_end: bool = True) -> str:
    """Return a draft well over the cap whose only matching sentence is the claim."""
    filler = [FILLER] * 30
    return " ".join([*filler, CLAIM] if claim_at_end else [CLAIM, *filler])


def test_the_cap_is_1200_characters() -> None:
    assert DRAFT_EXCERPT_CHARS == 1_200


def test_a_draft_that_fits_is_used_whole() -> None:
    assert select_draft_excerpt(f"  {CLAIM}  ", QUESTION) == CLAIM


def test_a_short_draft_is_used_whole_even_when_the_question_names_nothing() -> None:
    assert select_draft_excerpt(CLAIM, "Do the selected studies support my claim?") == CLAIM


def test_a_blank_draft_gives_no_excerpt() -> None:
    assert select_draft_excerpt("   \n ", QUESTION) == ""


def test_a_claim_at_the_end_of_a_long_draft_is_selected() -> None:
    draft = long_draft(claim_at_end=True)
    assert len(draft) > DRAFT_EXCERPT_CHARS

    assert select_draft_excerpt(draft, QUESTION) == CLAIM


def test_a_claim_at_the_start_of_a_long_draft_is_selected() -> None:
    assert select_draft_excerpt(long_draft(claim_at_end=False), QUESTION) == CLAIM


def test_words_match_by_their_stem() -> None:
    # "enrollment" in the question matches "enrolled" in the draft.
    assert select_draft_excerpt(long_draft(), "Is the enrollment right?") == CLAIM


def test_numbers_count_as_matches() -> None:
    draft = " ".join([FILLER] * 30 + ["A total of 18 were seen."])

    assert select_draft_excerpt(draft, "Does 18 hold?") == "A total of 18 were seen."


def test_no_matching_sentence_gives_no_excerpt() -> None:
    draft = " ".join([FILLER] * 30)

    assert select_draft_excerpt(draft, QUESTION) == ""


def test_a_question_with_only_generic_words_matches_nothing_in_a_long_draft() -> None:
    assert select_draft_excerpt(long_draft(), "Do the selected studies support my claim?") == ""


def test_the_excerpt_never_exceeds_the_cap_and_keeps_document_order() -> None:
    sentences = [f"Enrolled group {index} had {index} participants." for index in range(60)]
    draft = " ".join(sentences)

    excerpt = select_draft_excerpt(draft, QUESTION)

    assert 0 < len(excerpt) <= DRAFT_EXCERPT_CHARS
    chosen = [s for s in sentences if s in excerpt]
    assert chosen == sorted(chosen, key=sentences.index)
    assert excerpt == " ".join(chosen)


def test_a_later_sentence_wins_a_tie() -> None:
    draft = f"Enrolled first batch. {FILLER} Enrolled second batch."

    assert select_draft_excerpt(draft, "Who enrolled?", limit=30) == "Enrolled second batch."


def test_a_sentence_longer_than_the_cap_is_cut_when_nothing_else_fits() -> None:
    draft = "Enrolled " + "x" * 100 + ". " + FILLER

    assert select_draft_excerpt(draft, "Who enrolled?", limit=20) == draft[:20]


def test_a_long_sentence_is_skipped_when_a_better_fit_was_already_chosen() -> None:
    draft = f"Enrolled adults. Enrolled {'x' * 100}. {FILLER}"

    # The short sentence shares two words with the question and the long one only one.
    assert select_draft_excerpt(draft, "Who enrolled adults?", limit=40) == "Enrolled adults."


def test_with_a_quote_the_search_text_is_the_quote_then_the_question_and_no_draft() -> None:
    quote = "Children recovered in 5 days"
    draft = "Adults recovered in 8 days. Children recovered in 5 days."

    text = build_search_text("How does this compare?", quote=quote, draft=draft)

    assert text == f"{quote}\nHow does this compare?"
    assert "Adults" not in text


def test_with_a_quote_and_no_draft_the_search_text_is_the_quote_then_the_question() -> None:
    assert build_search_text("Compare?", quote="5 days") == "5 days\nCompare?"


def test_without_a_quote_the_question_is_followed_by_the_draft_excerpt() -> None:
    assert build_search_text(QUESTION, draft=CLAIM) == f"{QUESTION}\n{CLAIM}"


def test_without_a_draft_the_question_stands_alone() -> None:
    assert build_search_text(QUESTION) == QUESTION


def test_a_blank_draft_leaves_the_question_alone() -> None:
    assert build_search_text(QUESTION, draft="") == QUESTION


def test_a_long_draft_with_nothing_that_matches_leaves_the_question_alone() -> None:
    draft = " ".join([FILLER] * 30)

    assert build_search_text(QUESTION, draft=draft) == QUESTION


def test_the_search_text_for_a_long_draft_adds_at_most_the_cap() -> None:
    text = build_search_text(QUESTION, draft=long_draft())

    assert text == f"{QUESTION}\n{CLAIM}"
    assert len(text) - len(QUESTION) - 1 <= DRAFT_EXCERPT_CHARS
