"""Suggest a relevance threshold for the assistant from labelled passages.

Run from the repository root with GEMINI_API_KEY set in backend/.env:

    python scripts/calibrate_relevance_threshold.py [--data scripts/calibration/labelled_passages.json]

The script embeds each query (with its quote, as the assistant does) and each labelled passage
with the same Gemini embedding model that indexes the library, then scores every pair by cosine
similarity. Passages labelled supporting, qualifying or contradicting count as relevant, because
conflicting evidence must reach the model. Unrelated passages must fall below the threshold.

Even-numbered cases choose the threshold; odd-numbered cases only check it. Only the embedding
API is called, and only with the text in the data file. Nothing is written, and the assistant is
not reconfigured: set ASSISTANT_RELEVANCE_THRESHOLD yourself once you accept the suggestion.
"""

import argparse
import json
import math
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

Embedder = Callable[[list[str]], list[list[float]]]

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "scripts" / "calibration" / "labelled_passages.json"
RELEVANT_LABELS = {"supporting", "qualifying", "contradicting"}
UNRELATED = "unrelated"


@dataclass(frozen=True)
class Sample:
    """One query and passage pair with its cosine score."""

    label: str
    score: float
    text: str = field(default="", compare=False)

    @property
    def relevant(self) -> bool:
        """Return whether the passage should reach the model."""
        return self.label in RELEVANT_LABELS


@dataclass(frozen=True)
class Metrics:
    """How a threshold separates relevant from unrelated passages."""

    threshold: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int

    @property
    def recall(self) -> float:
        """Return the share of relevant passages kept."""
        relevant = self.true_positives + self.false_negatives
        return self.true_positives / relevant if relevant else 0.0

    @property
    def precision(self) -> float:
        """Return the share of kept passages that are relevant."""
        kept = self.true_positives + self.false_positives
        return self.true_positives / kept if kept else 0.0

    @property
    def false_positive_rate(self) -> float:
        """Return the share of unrelated passages kept."""
        unrelated = self.false_positives + self.true_negatives
        return self.false_positives / unrelated if unrelated else 0.0


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the cosine similarity of two vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def evaluate(samples: Sequence[Sample], threshold: float) -> Metrics:
    """Count the outcomes of keeping every passage scoring at or above ``threshold``."""
    tp = sum(1 for s in samples if s.relevant and s.score >= threshold)
    fp = sum(1 for s in samples if not s.relevant and s.score >= threshold)
    fn = sum(1 for s in samples if s.relevant and s.score < threshold)
    tn = sum(1 for s in samples if not s.relevant and s.score < threshold)
    return Metrics(threshold, tp, fp, fn, tn)


def choose_threshold(samples: Sequence[Sample]) -> float:
    """Return the cutoff that best separates relevant from unrelated passages.

    Every distinct score is a candidate, because the assistant keeps scores at or above the
    threshold. The best candidate maximizes recall minus the false positive rate. Ties go to
    the lower one, since dropping relevant evidence costs more than keeping an unrelated passage.
    The result sits halfway between that candidate and the next lower score, so it keeps a margin
    on both sides of the boundary.

    Raises:
        ValueError: If the samples lack relevant or unrelated passages.
    """
    if not any(s.relevant for s in samples) or all(s.relevant for s in samples):
        raise ValueError("Need both relevant and unrelated passages to choose a threshold.")
    scores = sorted({s.score for s in samples})

    def quality(threshold: float) -> tuple[float, float]:
        metrics = evaluate(samples, threshold)
        return metrics.recall - metrics.false_positive_rate, -threshold

    best = max(scores, key=quality)
    lower = [score for score in scores if score < best]
    return (best + lower[-1]) / 2 if lower else best


def split_cases(cases: Sequence[dict]) -> tuple[list[dict], list[dict]]:
    """Split cases into those that choose the threshold and those that only check it."""
    return list(cases[0::2]), list(cases[1::2])


def query_text(case: dict) -> str:
    """Return the text the assistant embeds for a case: the quote, then the question."""
    quote = case.get("quote")
    return f"{quote}\n{case['query']}" if quote else case["query"]


def score_cases(cases: Sequence[dict], embed: Embedder) -> list[Sample]:
    """Score every passage of every case against its query."""
    texts = [query_text(case) for case in cases]
    texts += [p["text"] for case in cases for p in case["passages"]]
    vectors = embed(texts)
    queries, passages = vectors[: len(cases)], iter(vectors[len(cases) :])
    return [
        Sample(p["label"], cosine(query, next(passages)), p["text"])
        for query, case in zip(queries, cases, strict=True)
        for p in case["passages"]
    ]


def gemini_embedder() -> Embedder:
    """Return an embedder backed by the assistant's Gemini embedding generator."""
    sys.path.insert(0, str(ROOT / "backend"))
    from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
        GeminiEmbeddingGenerator,
    )
    from domain.assistant.models.value_objects import Chunk, ChunkId

    generator = GeminiEmbeddingGenerator()
    print(f"Embedding model: {generator.model}")

    def embed(texts: list[str]) -> list[list[float]]:
        chunks = [Chunk(ChunkId.new(), text, "", "", "") for text in texts]
        return [e.vector for e in generator.generate(chunks)]

    return embed


def describe(name: str, metrics: Metrics) -> str:
    """Return one line summarizing a threshold on a set of samples."""
    return (
        f"{name}: threshold {metrics.threshold:.4f}  recall {metrics.recall:.2f}  "
        f"precision {metrics.precision:.2f}  unrelated kept {metrics.false_positive_rate:.2f}  "
        f"(kept {metrics.true_positives + metrics.false_positives}, "
        f"missed {metrics.false_negatives})"
    )


def label_ranges(samples: Sequence[Sample]) -> list[str]:
    """Return the lowest, mean and highest score of each label."""
    lines = []
    for label in ("supporting", "qualifying", "contradicting", UNRELATED):
        scores = [s.score for s in samples if s.label == label]
        if scores:
            lines.append(
                f"  {label:<14} n={len(scores):<3} min {min(scores):.3f}  "
                f"mean {sum(scores) / len(scores):.3f}  max {max(scores):.3f}"
            )
    return lines


def main() -> None:
    """Score the labelled passages and print the suggested threshold."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    cases = json.loads(parser.parse_args().data.read_text(encoding="utf-8"))
    calibration, held_out = split_cases(cases)

    embed = gemini_embedder()
    fit = score_cases(calibration, embed)
    check = score_cases(held_out, embed)

    threshold = choose_threshold(fit)
    print(f"\nScores by label ({len(calibration)} calibration cases):")
    print("\n".join(label_ranges(fit)))
    print()
    print(describe("calibration", evaluate(fit, threshold)))
    print(describe("held-out   ", evaluate(check, threshold)))
    for name, samples in (("calibration", fit), ("held-out", check)):
        for s in sorted(samples, key=lambda s: -s.score):
            if not s.relevant and s.score >= threshold:
                print(f"  unrelated kept ({name}): {s.score:.3f}  {s.text}")
    print(f"\nSuggested ASSISTANT_RELEVANCE_THRESHOLD={threshold:.4f}")


if __name__ == "__main__":
    main()
