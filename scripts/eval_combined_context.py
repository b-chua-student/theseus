"""Manual evaluation of the combined-context answers against the real Gemini models (T-012).

Run from the repository root with GEMINI_API_KEY set in backend/.env:

    python scripts/eval_combined_context.py [--threshold 0.69] [--only S-068]

It builds a small made-up library (Methods, Replication, Pilot), indexes it with the Gemini
embedding model, and asks the assistant the acceptance scenarios of
specs/assistant/combined_context/gherkin.feature through the real ChatService, retrieval, token
counter and Gemini chat model. Each scenario prints what the model was given and what it
answered, then a few automatic checks. The checks are keyword heuristics: read the answers.

Only the made-up text below is sent to Gemini. Nothing is written to disk.
"""

import argparse
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from domain.assistant.infrastructure.adapters.gemini_chat_model import GeminiChatModel  # noqa: E402
from domain.assistant.infrastructure.adapters.gemini_embedding_generator import (  # noqa: E402
    GeminiEmbeddingGenerator,
)
from domain.assistant.infrastructure.adapters.gemini_token_counter import (  # noqa: E402
    GeminiTokenCounter,
)
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (  # noqa: E402
    InMemoryConversationRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_indexed_document_repository import (  # noqa: E402
    InMemoryIndexedDocumentRepository,
)
from domain.assistant.infrastructure.adapters.in_memory_vector_store import (  # noqa: E402
    InMemoryVectorStore,
)
from domain.assistant.models.aggregates import IndexedDocument  # noqa: E402
from domain.assistant.models.errors import ChatModelError, EmbeddingGenerationError  # noqa: E402
from domain.assistant.models.value_objects import (  # noqa: E402
    Answer,
    Chunk,
    ChunkId,
    DocumentRefId,
    ExchangeContext,
    IndexedDocumentTitle,
    ProjectId,
)
from domain.assistant.services.chat import ChatService  # noqa: E402

CONTEXT_WINDOW = 1_048_576
RESPONSE_RESERVE = 16_384

LIBRARY = {
    "Methods": [
        "The trial enrolled 18 participants across two sites.",
        "Children recovered in a median of 7 days after treatment.",
        "The treatment effect appeared only in adults under 40; no effect was seen in older adults.",
        "Outcome assessors were blinded to treatment allocation.",
    ],
    "Replication": [
        "In the replication, the same trial enrolled 24 participants.",
        "The replication used the same randomization procedure as the original trial.",
    ],
    "Pilot": [
        "The pilot study enrolled 18 participants.",
        "In the pilot, children recovered in 3 days.",
    ],
}


def retry[T](call: Callable[[], T], attempts: int = 5, wait: float = 30.0) -> T:
    """Call ``call``, waiting and trying again when the provider is busy or rate limits."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except (ChatModelError, EmbeddingGenerationError) as exc:
            if attempt == attempts:
                raise
            print(f"  (provider error: {exc}; waiting {wait:.0f}s)")
            time.sleep(wait)
    raise AssertionError("unreachable")


class Library:
    """The made-up sources, indexed with the real embedding model."""

    def __init__(self, project: ProjectId, threshold: float) -> None:
        """Embed every passage once and wire a ChatService around the real Gemini adapters."""
        self.project = project
        self.documents = InMemoryIndexedDocumentRepository()
        self.vectors = InMemoryVectorStore()
        self.refs: dict[str, DocumentRefId] = {}
        self.stale: set[str] = set()
        embedder = GeminiEmbeddingGenerator()
        counter = GeminiTokenCounter()
        self.chunks = chunks_by_title = {
            title: [
                Chunk(ChunkId.new(), text, str(i), f"p{i}", text)
                for i, text in enumerate(texts, 1)
            ]
            for title, texts in LIBRARY.items()
        }
        every = [chunk for chunks in chunks_by_title.values() for chunk in chunks]
        vectors = {e.chunk_id: e for e in retry(lambda: embedder.generate(every))}
        for title, chunks in chunks_by_title.items():
            ref = DocumentRefId.new()
            self.refs[title] = ref
            document = IndexedDocument.create(IndexedDocumentTitle(title), ref, project)
            document.start_indexing()
            document.complete_indexing(chunks)
            self.documents.add(document)
            self.vectors.upsert(ref, [vectors[c.id] for c in chunks], chunks)
        self.service = ChatService(
            InMemoryConversationRepository(),
            GeminiChatModel(token_counter=counter, context_window=CONTEXT_WINDOW),
            embedding_generator=embedder,
            vector_store=self.vectors,
            document_repository=self.documents,
            source_ids=lambda _project: list(self.refs.values()),
            relevance_threshold=threshold,
            token_counter=counter,
            context_window=CONTEXT_WINDOW,
            response_reserve=RESPONSE_RESERVE,
        )

    def make_unavailable(self, title: str) -> None:
        """Mark a source as not searchable, as if it were being reindexed."""
        document = self.documents.get_by_doc_ref_id(self.refs[title])
        assert document is not None
        document.mark_stale()
        self.documents.save(document)
        self.stale.add(title)

    def restore_all(self) -> None:
        """Make every source searchable again."""
        for title in self.stale:
            document = self.documents.get_by_doc_ref_id(self.refs[title])
            assert document is not None
            document.start_indexing()
            document.complete_indexing(self.chunks[title])
            self.documents.save(document)
        self.stale.clear()

    def ask(
        self,
        question: str,
        *,
        sources: list[str],
        draft: str | None,
        quote: str | None = None,
        web: bool,
    ) -> Answer:
        """Ask in a fresh conversation with the given selection."""
        conversation = str(self.service.start(str(self.project.value)).value)
        context = ExchangeContext.decode(
            "source_library" if sources else "manuscript",
            manuscript_text=draft or "",
            source_ids=[str(self.refs[title].value) for title in sources] or None,
            quote=quote,
            web=web,
            manuscript=draft is not None,
        )
        return retry(lambda: self.service.ask(conversation, question, context=context))


@dataclass
class Scenario:
    """One acceptance scenario to ask, with keyword checks on the answer."""

    id: str
    title: str
    question: str
    sources: list[str]
    draft: str | None
    web: bool
    quote: str | None = None
    prepare: Callable[[Library], None] = lambda library: None
    expect: list[tuple[str, Callable[[str, Answer], bool]]] = field(default_factory=list)


def mentions(*words: str) -> Callable[[str, Answer], bool]:
    """Pass when every word appears in the answer."""
    return lambda text, _answer: all(w.lower() in text for w in words)


def omits(*words: str) -> Callable[[str, Answer], bool]:
    """Pass when no word appears in the answer."""
    return lambda text, _answer: not any(w.lower() in text for w in words)


def cites(title: str) -> Callable[[str, Answer], bool]:
    """Pass when a citation names ``title``."""
    return lambda _text, answer: any(c.title == title for c in answer.citations)


def not_cites(title: str) -> Callable[[str, Answer], bool]:
    """Pass when no citation names ``title``."""
    return lambda _text, answer: not any(c.title == title for c in answer.citations)


def matches(pattern: str) -> Callable[[str, Answer], bool]:
    """Pass when the regular expression matches the answer."""
    return lambda text, _answer: re.search(pattern, text, re.IGNORECASE) is not None


SCENARIOS = [
    Scenario(
        "S-068", "Which selected study supports the manuscript claim",
        "Which selected studies support my enrollment figure?",
        ["Methods", "Replication"], "The trial enrolled 18 participants.", web=False,
        expect=[
            ("names Methods as support", mentions("methods")),
            ("states Replication's 24", mentions("replication", "24")),
            ("cites Methods", cites("Methods")),
            ("does not mention or cite Pilot", lambda t, a: "pilot" not in t and not_cites("Pilot")(t, a)),
        ],
    ),
    Scenario(
        "S-069", "Address the quoted passage among two related claims",
        "How does this passage compare with Methods?",
        ["Methods"], "Adults recovered in 8 days. Children recovered in 5 days.", web=False,
        quote="Children recovered in 5 days",
        expect=[
            ("compares 5 and 7 days", mentions("5", "7")),
            ("does not discuss the adults' 8 days as the comparison", omits("8 days")),
            ("cites Methods", cites("Methods")),
        ],
    ),
    Scenario(
        "S-078", "A selected study qualifies the claim",
        "Do the selected studies support my claim?",
        ["Methods"], "The treatment works for all adults.", web=False,
        expect=[
            ("mentions under 40", matches(r"under\s*40|40")),
            ("does not call Methods contradicting", omits("contradicts the claim", "contradicting the claim")),
            ("cites Methods", cites("Methods")),
        ],
    ),
    Scenario(
        "S-072a", "Gap: one selected source unavailable",
        "Which selected studies support my enrollment figure?",
        ["Methods", "Replication"], "The trial enrolled 18 participants.", web=False,
        prepare=lambda lib: lib.make_unavailable("Replication"),
        expect=[
            ("cites Methods", cites("Methods")),
            ("says Replication could not be checked", matches(r"replication.*(could not|couldn.t|unable|unavailable)|(could not|couldn.t|unable|unavailable).*replication")),
        ],
    ),
    Scenario(
        "S-072b", "Gap: one selected source searched without a match",
        "Which selected studies support my claim that children recovered in 7 days?",
        ["Methods", "Replication"], "Children recovered in 7 days.", web=False,
        expect=[
            ("cites Methods", cites("Methods")),
            ("says no relevant passage in Replication", matches(r"replication.*(no relevant|not find|no passage|nothing)")),
        ],
    ),
    Scenario(
        "S-073", "None of the selected sources supplies usable evidence",
        "Do the selected studies support my claim that children recovered in 5 days?",
        ["Methods", "Replication"], "Children recovered in 5 days.", web=False,
        prepare=lambda lib: lib.make_unavailable("Methods"),
        expect=[
            ("says it could not be verified", matches(r"could not be verified|cannot be verified|couldn.t be verified|unable to verify|not be verified")),
            ("does not call the claim contradicted", omits("is contradicted", "contradicts your claim")),
            ("does not use Pilot", omits("pilot")),
        ],
    ),
    Scenario(
        "S-085", "General knowledge cannot stand in for missing source evidence",
        "Does Methods verify my claim that vitamin D prevents colds?",
        ["Methods"], "Vitamin D prevents colds.", web=True,
        expect=[
            ("names Methods and no relevant passage", matches(r"methods.*(no relevant|not find|no passage|nothing)|(no relevant|not find|no passage|nothing).*methods")),
            ("says it could not be verified", matches(r"could not be verified|cannot be verified|couldn.t be verified|not be verified|unable to verify")),
            ("labels general knowledge", matches(r"general knowledge")),
        ],
    ),
]


def run(library: Library, scenario: Scenario) -> bool:
    """Ask one scenario, print what happened, and return whether every check passed."""
    print(f"\n=== {scenario.id}: {scenario.title}")
    print(f"selection: web={scenario.web}, manuscript={scenario.draft is not None}, "
          f"sources={scenario.sources}")
    if scenario.draft is not None:
        print(f"draft: {scenario.draft}")
    if scenario.quote:
        print(f"quote: {scenario.quote}")
    print(f"question: {scenario.question}")
    answer = library.ask(
        scenario.question,
        sources=scenario.sources,
        draft=scenario.draft,
        quote=scenario.quote,
        web=scenario.web,
    )
    print("--- answer\n" + answer.text)
    print("--- citations: " + (", ".join(f"[{c.key}] {c.title}" for c in answer.citations) or "none"))
    text = answer.text.lower()
    passed = True
    for name, check in scenario.expect:
        ok = check(text, answer)
        passed = passed and ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return passed


def main() -> None:
    """Index the made-up library and run the scenarios."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--threshold", type=float, default=0.69)
    parser.add_argument("--only", help="Run one scenario, for example S-068.")
    args = parser.parse_args()

    chosen = [s for s in SCENARIOS if args.only in (None, s.id)]
    results = {}
    library = Library(ProjectId.new(), args.threshold)
    for scenario in chosen:
        library.restore_all()
        scenario.prepare(library)
        results[scenario.id] = run(library, scenario)
    print("\n=== summary")
    for scenario_id, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {scenario_id}")


if __name__ == "__main__":
    main()
