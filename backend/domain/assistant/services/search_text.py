"""The text embedded to search the selected library sources (D-003).

A question such as "Which selected studies support my enrollment figure?" does not say what the
claim is; the claim is in the draft. The search text therefore carries the claim too: the exact
quote when the writer quoted one, otherwise a bounded excerpt of the draft.
"""

import re

# The most draft text added to a search. An initial cap, to be revisited with measurements.
DRAFT_EXCERPT_CHARS = 1_200
# Words are compared by their first characters, so "enrollment" and "enrolled" match.
STEM_LENGTH = 5

_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD = re.compile(r"[a-z0-9]+")
# Words that open or pad a question without naming its subject.
_GENERIC = frozenset(
    {
        "and", "any", "are", "ask", "been", "can", "check", "claim", "claims", "compare",
        "could", "did", "does", "draft", "evidence", "figure", "figures", "for", "from",
        "how", "library", "manuscript", "our", "paper", "passage", "report", "reports",
        "say", "says", "selected", "source", "sources", "studies", "study", "support",
        "supported", "supports", "that", "the", "their", "there", "these", "this", "those",
        "verify", "was", "were", "what", "when", "where", "which", "whether", "who", "why",
        "with", "would", "you", "your",
    }
)  # fmt: skip


def _stems(text: str) -> set[str]:
    """Return the lightly stemmed content words of ``text``; numbers are kept."""
    stems = set()
    for word in _WORD.findall(text.lower()):
        if word in _GENERIC or (len(word) < 3 and not word.isdigit()):
            continue
        stems.add(word[:STEM_LENGTH])
    return stems


def select_draft_excerpt(draft: str, question: str, limit: int = DRAFT_EXCERPT_CHARS) -> str:
    """Return at most ``limit`` characters of ``draft`` that bear on ``question``.

    A draft that fits is returned whole. For a longer draft, its sentences are ranked by how
    many content words they share with the question, the best are taken until ``limit`` is
    reached (a later sentence wins a tie), and they are returned in document order. A sentence
    that alone exceeds ``limit`` is cut to it only when nothing better fits. If no sentence
    shares a word with the question, the result is empty.
    """
    text = draft.strip()
    if len(text) <= limit:
        return text
    wanted = _stems(question)
    if not wanted:
        return ""
    sentences = [s.strip() for s in _SENTENCE_BREAK.split(text) if s.strip()]
    ranked = sorted(
        ((len(wanted & _stems(sentence)), index) for index, sentence in enumerate(sentences)),
        reverse=True,
    )
    chosen: dict[int, str] = {}
    used = 0
    for score, index in ranked:
        if score == 0:
            break
        sentence = sentences[index]
        cost = len(sentence) + (1 if chosen else 0)
        if used + cost <= limit:
            chosen[index] = sentence
            used += cost
        elif not chosen:
            chosen[index] = sentence[:limit]
            used = limit
    return " ".join(chosen[index] for index in sorted(chosen))


def build_search_text(question: str, *, quote: str | None = None, draft: str | None = None) -> str:
    """Return the text to embed when searching the library for ``question``.

    With a quote, the text is the exact quote, then the question, and no other draft text is
    added. Otherwise, when ``draft`` is given (Manuscript is checked), the question is followed
    by the draft excerpt, or stands alone if the draft has nothing that matches. Without a
    draft, the question stands alone.
    """
    if quote:
        return f"{quote}\n{question}"
    excerpt = select_draft_excerpt(draft, question) if draft is not None else ""
    return f"{question}\n{excerpt}" if excerpt else question
