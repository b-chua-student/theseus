"""Conservative extractive checks shared by direct answers, proposals and recovery."""

import re
from calendar import month_name
from dataclasses import dataclass

from domain.assistant.models.value_objects import Evidence, Finding, ProposedFinding, Verdict

_MONTH = "|".join(month_name[1:])
_DATE = rf"(?:{_MONTH})(?: \d{{1,2}})?(?:,? \d{{4}})?|\d{{4}}"
_EVENT = re.compile(
    rf"(?:the )?(?P<subject>[\w -]+?) (?P<event>started|ended) "
    rf"(?:in|on) (?P<value>{_DATE})[.]?",
    re.I,
)
_SUBJECT = r"(?P<subject>[\w -]+?)"
_EVENT_QUESTION = re.compile(
    rf"(?:when|(?:in )?what (?P<precision>year|month|day)) did (?:the )?{_SUBJECT} "
    r"(?P<events>start and end|start|end)(?P<year>,? and in what year did it end)?\??",
    re.I,
)
_YES_NO = re.compile(
    rf"did (?:the )?{_SUBJECT} (?P<events>start|end) (?:on|in) (?P<date>{_DATE})\??", re.I
)
_ATTRIBUTE = re.compile(r"what (?:is|was) (?:the )?(?P<attribute>[\w -]+ of [\w -]+)\??", re.I)


@dataclass(frozen=True)
class _Fact:
    subject: str
    relation: str
    value: str


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _fact(sentence: str) -> _Fact | None:
    if event := _EVENT.fullmatch(sentence):
        return _Fact(event["subject"].lower(), event["event"].lower(), event["value"].lower())
    attr = re.fullmatch(
        r"(?:the )?([\w -]+ of [\w -]+?) (?:is|was) ([\w $%,-]+)\.?", sentence, re.I
    )
    if attr:
        return _Fact(attr[1].lower(), "attribute", attr[2].lower())
    return None


def _requested(question: str) -> tuple[str, list[str], str]:
    question = question.strip()
    event = _EVENT_QUESTION.fullmatch(question)
    yes_no = _YES_NO.fullmatch(question)
    if match := event or yes_no:
        relations = [
            "started" if verb == "start" else "ended"
            for verb in match["events"].lower().split(" and ")
        ]
        precision = ""
        if event:
            precision = "end year" if event["year"] else (event["precision"] or "").lower()
        elif yes_no:
            precision = yes_no["date"].lower()
        return match["subject"].lower(), relations, precision
    if attr := _ATTRIBUTE.fullmatch(question):
        return attr["attribute"].lower(), ["attribute"], ""
    return "", [], ""


def _sufficient(value: str, detail: str) -> bool:
    if detail == "year":
        return bool(re.search(r"\b\d{4}\b", value))
    if detail == "day":
        return bool(re.search(r"\b\d{1,2}\b", value))
    if detail == "month":
        return bool(re.search(rf"\b(?:{_MONTH})\b", value, re.I))
    return not detail or detail == value


def check_evidence(
    question: str,
    evidence: Evidence,
    *,
    proposals: tuple[ProposedFinding, ...] | None = None,
    manuscript_text: str = "",
) -> Verdict:
    """Verify whole sentences against their own passages and the requested subject and relation."""
    subject, relations, detail = _requested(question)
    if not relations:
        return Verdict(unresolved=(question,), missing_evidence=question)

    matches: dict[str, list[tuple[_Fact, Finding]]] = {relation: [] for relation in relations}
    competing_relations = set()
    for key, passage in enumerate(evidence.passages, 1):
        for sentence in _sentences(passage.text):
            fact = _fact(sentence)
            if fact is None or fact.relation not in matches:
                continue
            if fact.subject != subject:
                competing_relations.add(fact.relation)
                continue
            matches[fact.relation].append((fact, Finding(sentence, key)))

    verified = []
    missing = []
    for relation, candidates in matches.items():
        values = {fact.value for fact, _ in candidates}
        if len(values) != 1 or (proposals is None and relation in competing_relations):
            missing.append(f"{subject} {relation}")
            continue
        for fact, finding in candidates:
            if proposals is not None and not any(
                p.citation == finding.citation
                and p.excerpt == finding.claim
                and p.text.rstrip(".") == finding.claim.rstrip(".")
                for p in proposals
            ):
                continue
            verified.append(finding)
            precision = detail
            if detail == "end year":
                precision = "year" if relation == "ended" else ""
            if not _sufficient(fact.value, precision):
                missing.append(f"{subject} {relation}: {precision}")
            break
        else:
            missing.append(f"{subject} {relation}")

    for sentence in _sentences(manuscript_text):
        fact = _fact(sentence)
        if fact and fact.subject == subject and fact.relation in relations:
            verified.append(Finding(sentence, None, "manuscript"))
    return Verdict(
        verified=tuple(verified),
        unresolved=tuple(missing),
        missing_evidence=", ".join(missing) or None,
    )
