"""Deterministic, side-effect-free three-way section merge."""

from dataclasses import dataclass, replace
from typing import Literal
from uuid import UUID

from .value_objects import SectionSnapshot, Snapshot

Choice = Literal["target", "source"]
FIELDS = ("heading", "body", "parent_id", "ordinal")


@dataclass(frozen=True)
class Resolution:
    section_id: UUID
    field: str
    choice: Choice


@dataclass(frozen=True)
class Conflict:
    section_id: UUID
    section_heading: str
    field: str
    kind: str
    base: object
    target: object
    source: object


@dataclass(frozen=True)
class Merged:
    snapshot: Snapshot


@dataclass(frozen=True)
class Conflicts:
    conflicts: list[Conflict]


def normalize(snapshot: Snapshot) -> Snapshot:
    groups: dict[UUID | None, list[SectionSnapshot]] = {}
    for section in snapshot.sections:
        groups.setdefault(section.parent_id, []).append(section)
    ranked = {}
    for siblings in groups.values():
        for rank, section in enumerate(sorted(siblings, key=lambda s: (s.ordinal, s.id))):
            ranked[section.id] = replace(section, ordinal=rank)
    result, visited = [], set()

    def visit(section):
        if section.id in visited:
            return
        visited.add(section.id)
        result.append(ranked[section.id])
        for child in sorted(groups.get(section.id, []), key=lambda s: (s.ordinal, s.id)):
            visit(child)

    for section in sorted(groups.get(None, []), key=lambda s: (s.ordinal, s.id)):
        visit(section)
    # Preserve invalid structures for conflict reporting, never silently drop them.
    for sid in sorted(ranked):
        visit(ranked[sid])
    return Snapshot(tuple(result))


def merge3(base, target, source):
    if target == source or source == base:
        return target, False
    if target == base:
        return source, False
    return target, True


def _values(section):
    return {field: getattr(section, field) for field in FIELDS} if section else None


def _descendants(sid, sections):
    found = {sid}
    while True:
        more = {s.id for s in sections.values() if s.parent_id in found} - found
        if not more:
            return found
        found.update(more)


def _merge(base, target, source, resolutions):
    b, t, s = ({x.id: x for x in normalize(snap).sections} for snap in (base, target, source))
    choices = {(r.section_id, r.field): r.choice for r in resolutions}
    result, conflicts, deletions = {}, [], []

    def conflict(sid, field, kind, bv, tv, sv):
        c = Conflict(sid, (t.get(sid) or s.get(sid) or b[sid]).heading, field, kind, bv, tv, sv)
        choice = choices.get((sid, field))
        if choice is None:
            conflicts.append(c)
        return sv if choice == "source" else tv

    for sid in sorted(b.keys() | t.keys() | s.keys()):
        bv, tv, sv = b.get(sid), t.get(sid), s.get(sid)
        if bv and (tv is None or sv is None):
            other = tv or sv
            if other is None or other == bv:
                continue
            chosen = conflict(
                sid,
                "section",
                "deleted_in_target" if tv is None else "deleted_in_source",
                _values(bv),
                _values(tv),
                _values(sv),
            )
            if chosen is not None:
                result[sid] = SectionSnapshot(id=sid, **chosen)
            if (sid, "section") in choices:
                deletions.append((sid, choices[sid, "section"]))
        elif tv is None or sv is None:
            result[sid] = tv or sv
        else:
            values = {}
            for field in FIELDS:
                v, differs = merge3(
                    getattr(bv, field) if bv else None, getattr(tv, field), getattr(sv, field)
                )
                if differs:
                    v = conflict(
                        sid,
                        field,
                        "field_conflict",
                        getattr(bv, field) if bv else None,
                        getattr(tv, field),
                        getattr(sv, field),
                    )
                values[field] = v
            result[sid] = SectionSnapshot(id=sid, **values)
    # Resolve ancestors first: a whole-subtree decision dominates child choices.
    tree = {**b, **t, **s, **result}

    def depth(sid):
        seen = set()
        while sid in tree and sid not in seen:
            seen.add(sid)
            sid = tree[sid].parent_id
        return len(seen)

    covered = set()
    for sid, choice in sorted(deletions, key=lambda item: (depth(item[0]), item[0])):
        if sid in covered:
            continue
        side = s if choice == "source" else t
        if sid not in side:
            removed = _descendants(sid, {**b, **t, **s, **result})
            for child in removed:
                result.pop(child, None)
            conflicts = [c for c in conflicts if c.section_id not in removed]
            covered.update(removed)
        else:
            kept = _descendants(sid, side)
            result.update({child: side[child] for child in kept})
            conflicts = [c for c in conflicts if c.section_id not in kept]
            covered.update(kept)
    # Structural resolutions select the side's parent link.
    for sid, field in choices:
        if field == "parent_id" and sid in result and sid not in covered:
            side = s if choices[sid, field] == "source" else t
            if sid in side:
                result[sid] = replace(result[sid], parent_id=side[sid].parent_id)
    structural = {}
    for sid, section in result.items():
        if section.parent_id is not None and section.parent_id not in result:
            structural[sid] = "parent_missing"
        path = []
        current = sid
        while current in result and current not in path:
            path.append(current)
            current = result[current].parent_id
        if current in path:
            cycle = path[path.index(current) :]
            affected = [
                x for x in cycle if x in s and (x not in b or s[x].parent_id != b[x].parent_id)
            ]
            for x in affected or cycle:
                structural[x] = "parent_cycle"
    for sid, kind in structural.items():
        if any(c.section_id == sid and c.field == "parent_id" for c in conflicts):
            continue
        conflicts.append(
            Conflict(
                sid,
                result[sid].heading,
                "parent_id",
                kind,
                b[sid].parent_id if sid in b else None,
                t[sid].parent_id if sid in t else None,
                s[sid].parent_id if sid in s else None,
            )
        )
    if conflicts:
        return Conflicts(sorted(conflicts, key=lambda c: (c.section_id, c.field)))
    return Merged(normalize(Snapshot(tuple(result.values()))))


def detect_conflicts(base, target, source):
    outcome = _merge(base, target, source, ())
    return outcome.conflicts if isinstance(outcome, Conflicts) else []


def merge_snapshots(base, target, source, resolutions=()):
    return _merge(base, target, source, resolutions)
