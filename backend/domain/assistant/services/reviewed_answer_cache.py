"""Per-chat-service cache for fully reviewed Source Library answers."""

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock

from domain.assistant.models.value_objects import Answer, Evidence


def fingerprint(*parts: object) -> str:
    """Hash ordered, JSON-compatible inputs without retaining prompt text in keys."""
    return hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()


def evidence_key(evidence: Evidence) -> str:
    """Include the identity, text, ordering and citation metadata of admitted passages."""
    return fingerprint(
        [
            (str(p.doc_ref_id.value), str(p.chunk_id.value), p.text, p.position, p.location)
            for p in evidence.passages
        ]
    )


@dataclass(frozen=True)
class Recovery:
    """One search to replay before reusing a recovered answer."""

    query: str
    keep: frozenset[int]
    evidence_key: str


@dataclass(frozen=True)
class ReviewedAnswer:
    """Fully reviewed findings and their retrieval dependencies."""

    answer: Answer
    recovery: tuple[Recovery, ...]


class ReviewedAnswerCache:
    """Bounded LRU, owned by a single service and its configured model and prompts."""

    def __init__(self, capacity: int = 128) -> None:
        """Keep at most capacity entries per worker."""
        self._entries: OrderedDict[str, ReviewedAnswer] = OrderedDict()
        self._capacity = capacity
        self._lock = Lock()

    def get(self, key: str) -> ReviewedAnswer | None:
        """Look up and promote an entry under the lock."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                self._entries.move_to_end(key)
            return entry

    def put(self, key: str, entry: ReviewedAnswer) -> None:
        """Publish a saved success and evict the oldest entry if necessary."""
        with self._lock:
            self._entries[key] = entry
            self._entries.move_to_end(key)
            if len(self._entries) > self._capacity:
                self._entries.popitem(last=False)
