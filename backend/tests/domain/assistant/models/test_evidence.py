"""Tests for evidence: stable passage keys, merging by identity and citation resolution."""

from domain.assistant.models.value_objects import Evidence
from tests.domain.assistant.validation_support import passage

P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
P3 = passage("P3", "The pilot was sponsored by the university.")
P4 = passage("P4", "The pilot enrolled forty patients.")


def locations(evidence: Evidence) -> list[str]:
    return [p.location for p in evidence.passages]


def test_s005_new_passages_are_added_after_retained_ones() -> None:
    merged = Evidence((P1,)).merge([P2, P1], limit=5)

    assert locations(merged) == ["P1", "P2"]


def test_s005_a_retained_passage_keeps_its_key_when_the_search_ranks_it_differently() -> None:
    merged = Evidence((P1,)).merge([P2, P1], limit=5)

    assert [c.key for c in merged.citations_for("May [1], July [2]")] == [1, 2]
    assert merged.passages[0].chunk_id == P1.chunk_id


def test_merging_nothing_leaves_the_evidence_unchanged() -> None:
    evidence = Evidence((P1, P2))

    assert evidence.merge([], limit=5) == evidence


def test_the_evidence_budget_limits_each_revised_draft() -> None:
    merged = Evidence((P1, P2)).merge([P3], limit=2)

    assert locations(merged) == ["P1", "P2"]


def test_the_evidence_budget_still_admits_new_passages_while_room_remains() -> None:
    merged = Evidence((P1,)).merge([P2, P3], limit=2)

    assert locations(merged) == ["P1", "P2"]


def test_s004_citations_resolve_to_the_admitted_passages_in_order_of_appearance() -> None:
    evidence = Evidence((P1, P2))

    citations = evidence.citations_for("July [2], and May [1]. Again July [2].")

    assert [(c.key, c.location) for c in citations] == [(2, "P2"), (1, "P1")]
    assert citations[0].chunk_id == P2.chunk_id
    assert citations[0].doc_ref_id == P2.doc_ref_id


def test_citations_to_passages_that_were_not_admitted_are_dropped() -> None:
    evidence = Evidence((P1,))

    assert [c.key for c in evidence.citations_for("May [1], July [2], other [0].")] == [1]


def test_text_without_citation_keys_has_no_citations() -> None:
    assert Evidence((P1,)).citations_for("No citations here.") == ()


def test_s005_a_full_evidence_set_gives_up_an_uncited_passage_for_a_new_one() -> None:
    merged = Evidence((P1, P2, P3)).merge([P4], limit=3, keep=[1])

    assert locations(merged) == ["P1", "P2", "P4"]


def test_s005_a_cited_passage_is_never_given_up_and_keeps_its_key() -> None:
    merged = Evidence((P1, P2, P3)).merge([P4], limit=3, keep=[1, 3])

    assert locations(merged) == ["P1", "P4", "P3"]


def test_a_full_evidence_set_with_every_passage_cited_admits_nothing() -> None:
    evidence = Evidence((P1, P2))

    assert evidence.merge([P3], limit=2, keep=[1, 2]) == evidence


def test_a_passage_admitted_by_a_merge_is_not_given_up_within_the_same_merge() -> None:
    merged = Evidence((P1, P2)).merge([P3, P4], limit=2, keep=[1])

    assert locations(merged) == ["P1", "P3"]


def test_without_keep_a_full_evidence_set_gives_up_nothing() -> None:
    evidence = Evidence((P1, P2))

    assert evidence.merge([P3], limit=2) == evidence
