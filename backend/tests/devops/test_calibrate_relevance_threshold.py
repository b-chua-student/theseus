"""Tests for the relevance-threshold calibration script (no API key needed)."""

import pytest
from scripts.calibrate_relevance_threshold import (
    Sample,
    choose_threshold,
    cosine,
    evaluate,
    query_text,
    score_cases,
    split_cases,
)


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


def test_cases_alternate_between_calibration_and_held_out() -> None:
    cases = [{"n": i} for i in range(5)]

    calibration, held_out = split_cases(cases)

    assert [c["n"] for c in calibration] == [0, 2, 4]
    assert [c["n"] for c in held_out] == [1, 3]


def test_the_query_text_puts_the_quote_before_the_question() -> None:
    assert query_text({"query": "Compare?", "quote": "5 days"}) == "5 days\nCompare?"
    assert query_text({"query": "Compare?"}) == "Compare?"


def test_cases_are_scored_against_their_own_query() -> None:
    cases = [
        {"query": "q1", "passages": [{"label": "supporting", "text": "p1"}]},
        {"query": "q2", "passages": [{"label": "unrelated", "text": "p2"}]},
    ]
    vectors = {"q1": [1.0, 0.0], "q2": [0.0, 1.0], "p1": [1.0, 0.0], "p2": [1.0, 0.0]}

    samples = score_cases(cases, lambda texts: [vectors[t] for t in texts])

    assert [s.label for s in samples] == ["supporting", "unrelated"]
    assert [s.score for s in samples] == [pytest.approx(1.0), pytest.approx(0.0)]
