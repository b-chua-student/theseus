"""Tests for the relevance-threshold calibration script (no API key needed)."""

import json
from pathlib import Path

import pytest
from scripts.calibrate_relevance_threshold import (
    DEFAULT_DATA,
    FILLER,
    Sample,
    admitted,
    case_draft,
    choose_threshold,
    cosine,
    evaluate,
    missed,
    query_text,
    score_all,
    split_indices,
)

from domain.assistant.services.search_text import DRAFT_EXCERPT_CHARS


def test_cosine_of_parallel_and_orthogonal_vectors() -> None:
    assert cosine([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 3.0]) == pytest.approx(0.0)
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_a_score_at_the_threshold_is_kept() -> None:
    samples = [Sample("supporting", 0.6), Sample("unrelated", 0.4)]

    metrics = evaluate(samples, 0.6)

    assert (metrics.true_positives, metrics.false_negatives) == (1, 0)
    assert (metrics.false_positives, metrics.true_negatives) == (0, 1)
    assert evaluate(samples, 0.61).recall == 0.0


def test_the_threshold_separates_relevant_from_unrelated_with_a_margin() -> None:
    samples = [
        Sample("supporting", 0.8),
        Sample("contradicting", 0.6),
        Sample("unrelated", 0.4),
        Sample("unrelated", 0.2),
    ]

    threshold = choose_threshold(samples)

    assert threshold == pytest.approx(0.5)
    metrics = evaluate(samples, threshold)
    assert metrics.recall == 1.0
    assert metrics.false_positive_rate == 0.0


def test_overlapping_scores_favor_recall_on_a_tie() -> None:
    samples = [
        Sample("supporting", 0.9),
        Sample("qualifying", 0.3),
        Sample("unrelated", 0.5),
        Sample("unrelated", 0.1),
    ]

    # Keeping >= 0.9 gives recall 0.5 and no false positives; keeping >= 0.3 gives recall 1.0 with
    # one false positive of two. Both score 0.5, and the lower candidate wins.
    assert choose_threshold(samples) < 0.3


def test_a_set_without_both_kinds_of_passage_cannot_be_calibrated() -> None:
    with pytest.raises(ValueError, match="relevant and unrelated"):
        choose_threshold([Sample("supporting", 0.9)])
    with pytest.raises(ValueError, match="relevant and unrelated"):
        choose_threshold([Sample("unrelated", 0.1)])


def test_the_misses_and_admissions_are_listed_worst_first() -> None:
    samples = [
        Sample("supporting", 0.9, "kept"),
        Sample("qualifying", 0.5, "near miss"),
        Sample("contradicting", 0.3, "far miss"),
        Sample("unrelated", 0.7, "leak"),
        Sample("unrelated", 0.8, "worse leak"),
        Sample("unrelated", 0.1, "excluded"),
    ]

    assert [s.text for s in missed(samples, 0.6)] == ["far miss", "near miss"]
    assert [s.text for s in admitted(samples, 0.6)] == ["worse leak", "leak"]


def test_cases_alternate_in_pairs_so_each_set_mixes_every_kind_of_case() -> None:
    fit, check = split_indices(8)

    assert fit == [0, 1, 4, 5]
    assert check == [2, 3, 6, 7]


def test_the_labelled_data_gives_both_sets_quote_and_draft_cases() -> None:
    cases = json.loads(Path(DEFAULT_DATA).read_text(encoding="utf-8"))
    fit, check = split_indices(len(cases))

    for indices in (fit, check):
        assert any("quote" in cases[i] for i in indices)
        assert any("draft" in cases[i] for i in indices)
        assert any(cases[i].get("filler_sentences") for i in indices)
    assert len(cases) + sum(len(c["passages"]) for c in cases) <= 100  # one embedding request


def test_the_search_text_is_the_production_text() -> None:
    quote = {"query": "Compare?", "quote": "5 days", "draft": "ignored"}
    draft = {"query": "Which studies support my enrollment figure?", "draft": "We enrolled 18."}
    plain = {"query": "What is entropy?"}

    assert query_text(quote) == "5 days\nCompare?"
    assert query_text(draft) == "Which studies support my enrollment figure?\nWe enrolled 18."
    assert query_text(plain) == "What is entropy?"


def test_a_long_draft_puts_the_claim_at_the_end_and_the_excerpt_selects_it() -> None:
    case = {
        "query": "Which selected studies support my fatigue finding?",
        "draft": "Iron reduced fatigue.",
        "filler_sentences": 30,
    }

    assert case_draft(case) == " ".join([FILLER] * 30 + ["Iron reduced fatigue."])
    assert len(case_draft(case) or "") > DRAFT_EXCERPT_CHARS
    assert (
        query_text(case)
        == "Which selected studies support my fatigue finding?\nIron reduced fatigue."
    )


def test_every_labelled_long_draft_is_longer_than_the_cap() -> None:
    cases = json.loads(Path(DEFAULT_DATA).read_text(encoding="utf-8"))

    for case in (c for c in cases if c.get("filler_sentences")):
        assert len(case_draft(case) or "") > DRAFT_EXCERPT_CHARS


def test_all_cases_are_scored_in_one_embedding_call_against_their_own_query() -> None:
    cases = [
        {"query": "q1", "passages": [{"label": "supporting", "text": "p1"}]},
        {"query": "q2", "passages": [{"label": "unrelated", "text": "p2"}]},
    ]
    vectors = {"q1": [1.0, 0.0], "q2": [0.0, 1.0], "p1": [1.0, 0.0], "p2": [1.0, 0.0]}
    calls: list[list[str]] = []

    def embed(texts: list[str]) -> list[list[float]]:
        calls.append(texts)
        return [vectors[t] for t in texts]

    scored = score_all(cases, embed)

    assert len(calls) == 1
    assert calls[0] == ["q1", "q2", "p1", "p2"]
    assert [[s.label for s in case] for case in scored] == [["supporting"], ["unrelated"]]
    assert [s.score for case in scored for s in case] == [pytest.approx(1.0), pytest.approx(0.0)]
    assert [s.case for case in scored for s in case] == [0, 1]
