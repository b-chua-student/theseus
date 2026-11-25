"""Suggest a relevance threshold for the assistant from labelled passages.

Run from the repository root with GEMINI_API_KEY set in backend/.env:

    python scripts/calibrate_relevance_threshold.py [--data scripts/calibration/labelled_passages.json]

Each case is scored with the exact text the assistant searches with: the production
``build_search_text`` applied to the case's question, its quote and its draft. A case with a
quote searches with the quote and question. A case with a draft searches with the question and a
draft excerpt of at most 1,200 characters; ``filler_sentences`` puts that many unrelated
sentences before the draft's claim, to make a long draft whose claim is at the end.

The query and every labelled passage are embedded with the Gemini embedding model that indexes
the library, in a single embedding request with no retries, and scored by cosine similarity.
Passages labelled supporting, qualifying or contradicting count as relevant, because conflicting
evidence must reach the model. Unrelated passages must fall below the threshold.

Cases are split in alternating pairs: the first two choose the threshold, the next two only
check it, and so on, so that both sets mix the question-only, quote and draft cases. Nothing is
written and the assistant is not reconfigured: set ASSISTANT_RELEVANCE_THRESHOLD yourself.
"""

import argparse
import json
import math
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.genai import types

    from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
        EmbeddingModels,
    )

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from domain.assistant.services.search_text import build_search_text  # noqa: E402

Embedder = Callable[[list[str]], list[list[float]]]

DEFAULT_DATA = ROOT / "scripts" / "calibration" / "labelled_passages.json"
RELEVANT_LABELS = {"supporting", "qualifying", "contradicting"}
UNRELATED = "unrelated"
FILLER = "The weather station recorded the readings each morning."


@dataclass(frozen=True)
class Sample:
    """One query and passage pair with its cosine score."""

    label: str
    score: float
    text: str = field(default="", compare=False)
    case: int = field(default=-1, compare=False)

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


def missed(samples: Sequence[Sample], threshold: float) -> list[Sample]:
    """Return the relevant passages the threshold would drop, lowest first."""
    return sorted((s for s in samples if s.relevant and s.score < threshold), key=lambda s: s.score)


def admitted(samples: Sequence[Sample], threshold: float) -> list[Sample]:
    """Return the unrelated passages the threshold would keep, highest first."""
    return sorted(
        (s for s in samples if not s.relevant and s.score >= threshold),
        key=lambda s: -s.score,
    )


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


def split_indices(count: int) -> tuple[list[int], list[int]]:
    """Return the case indices that choose the threshold and those that only check it.

    Cases alternate in pairs, so each set mixes the question-only, quote and draft cases.
    """
    fit = [i for i in range(count) if i % 4 in (0, 1)]
    check = [i for i in range(count) if i % 4 in (2, 3)]
    return fit, check


def case_draft(case: dict) -> str | None:
    """Return a case's draft, with any filler sentences before its claim, or None."""
    draft = case.get("draft")
    if draft is None:
        return None
    return " ".join([*([FILLER] * case.get("filler_sentences", 0)), draft])


def query_text(case: dict) -> str:
    """Return the exact text the assistant embeds when it searches for a case."""
    return build_search_text(case["query"], quote=case.get("quote"), draft=case_draft(case))


def score_all(cases: Sequence[dict], embed: Embedder) -> list[list[Sample]]:
    """Score every passage of every case against its query, in one embedding call."""
    texts = [query_text(case) for case in cases]
    texts += [p["text"] for case in cases for p in case["passages"]]
    vectors = embed(texts)
    queries, passages = vectors[: len(cases)], iter(vectors[len(cases) :])
    return [
        [Sample(p["label"], cosine(query, next(passages)), p["text"], index) for p in case["passages"]]
        for index, (query, case) in enumerate(zip(queries, cases, strict=True))
    ]


class CountingEmbeddingModels:
    """Passes embedding requests through to Gemini and counts them."""

    def __init__(self, models: "EmbeddingModels") -> None:
        self._models = models
        self.requests = 0

    def embed_content(
        self, *, model: str, contents: list[str], config: "types.EmbedContentConfig"
    ) -> "types.EmbedContentResponse":
        """Count the request, then send it."""
        self.requests += 1
        return self._models.embed_content(model=model, contents=contents, config=config)


class CountingEmbeddingClient:
    """A Gemini client whose embedding requests are counted."""

    def __init__(self, models: CountingEmbeddingModels, owner: object) -> None:
        self._models = models
        # The real client closes its HTTP connection when it is garbage-collected, so keep it.
        self._owner = owner

    @property
    def models(self) -> CountingEmbeddingModels:
        """Return the counting models API."""
        return self._models


def gemini_embedder() -> tuple[Embedder, Callable[[], int]]:
    """Return an embedder backed by Gemini and a function counting its API requests.

    The key is read from backend/.env and never printed. The Gemini client makes one attempt
    per request, so nothing is retried.
    """
    import os

    from dotenv import load_dotenv
    from google import genai
    from google.genai import types

    from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (
        GeminiEmbeddingGenerator,
    )
    from domain.assistant.models.value_objects import Chunk, ChunkId

    load_dotenv(ROOT / "backend" / ".env")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set in backend/.env")
    real = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30_000))
    counting = CountingEmbeddingModels(real.models)
    generator = GeminiEmbeddingGenerator(client=CountingEmbeddingClient(counting, real))
    print(f"Embedding model: {generator.model}")

    def embed(texts: list[str]) -> list[list[float]]:
        chunks = [Chunk(ChunkId.new(), text, "", "", "") for text in texts]
        return [e.vector for e in generator.generate(chunks)]

    return embed, lambda: counting.requests


def describe(name: str, metrics: Metrics) -> str:
    """Return one line summarizing a threshold on a set of samples."""
    return (
        f"{name}: threshold {metrics.threshold:.4f}  recall {metrics.recall:.2f}  "
        f"precision {metrics.precision:.2f}  unrelated kept {metrics.false_positive_rate:.2f}  "
        f"(relevant missed {metrics.false_negatives}, unrelated admitted {metrics.false_positives})"
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


def sweep(samples: Sequence[Sample], start: float = 0.60, stop: float = 0.90) -> list[str]:
    """Return a table of recall and unrelated-kept for evenly spaced cutoffs."""
    lines = ["  cutoff  relevant kept  unrelated kept"]
    for step in range(round((stop - start) / 0.025) + 1):
        threshold = start + step * 0.025
        metrics = evaluate(samples, threshold)
        lines.append(
            f"  {threshold:.3f}  {metrics.true_positives:>3}/{metrics.true_positives + metrics.false_negatives:<3}"
            f"        {metrics.false_positives:>3}/{metrics.false_positives + metrics.true_negatives:<3}"
        )
    return lines


def report_set(name: str, samples: Sequence[Sample], threshold: float) -> None:
    """Print how a threshold does on one set, naming each miss and each admission."""
    print(describe(name, evaluate(samples, threshold)))
    for s in missed(samples, threshold):
        print(f"  MISSED relevant  ({s.label}) {s.score:.3f}  case {s.case}: {s.text}")
    for s in admitted(samples, threshold):
        print(f"  ADMITTED unrelated {s.score:.3f}  case {s.case}: {s.text}")


def main() -> None:
    """Score the labelled passages and print the suggested threshold."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    cases = json.loads(parser.parse_args().data.read_text(encoding="utf-8"))
    fit_index, check_index = split_indices(len(cases))

    embed, requests = gemini_embedder()
    scored = score_all(cases, embed)
    fit = [s for i in fit_index for s in scored[i]]
    check = [s for i in check_index for s in scored[i]]

    threshold = choose_threshold(fit)
    print(f"\nScores by label ({len(fit_index)} calibration cases):")
    print("\n".join(label_ranges(fit)))
    print(f"\nScores by label ({len(check_index)} held-out cases):")
    print("\n".join(label_ranges(check)))
    print(f"\nChosen on the calibration cases: {threshold:.4f}\n")
    report_set("calibration", fit, threshold)
    report_set("held-out   ", check, threshold)
    print("\nAll cases pooled:")
    print("\n".join(sweep(fit + check)))
    print(f"\nEmbedding requests used: {requests()}")
    print(f"Suggested ASSISTANT_RELEVANCE_THRESHOLD={threshold:.4f}")


if __name__ == "__main__":
    main()
