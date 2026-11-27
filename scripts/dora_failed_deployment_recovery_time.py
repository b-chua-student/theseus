"""Report recovery times from maintainer-confirmed production incidents."""

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError

if TYPE_CHECKING or __package__:
    from . import dora_change_failure_rate as cfr
    from .dora_evidence import EvidenceError, timestamp
else:
    import dora_change_failure_rate as cfr
    from dora_evidence import EvidenceError, timestamp

LABEL = "dora-recovery-incident"
CONFIRMATION = "DORA recovery:"
TIMELINE = "DORA recovery timeline:"
LINK = re.compile(rf"DORA corrective deploy:[ \t]*({cfr.DEPLOY})[ \t]*")
MARKER = re.compile(rf"<!-- dora-correction [^/\s]+/({cfr.DEPLOY}) -->")
FLAGS = ("degraded", "deploymentCaused", "immediateIntervention", "restored")


@dataclass
class Claim:
    """Track one timestamp and whether later evidence disputes it."""

    time: datetime | None = None
    disputed: bool = False

    def apply(self, instant: datetime, *, resolves: bool) -> None:
        """Apply a valid claim in comment order."""
        if resolves or self.time is None:
            self.time = instant
            self.disputed = False
        elif self.time != instant:
            self.disputed = True


@dataclass(frozen=True)
class Recovery:
    """One qualifying issue and its reportable outcome."""

    number: int
    status: str
    minutes: float | None = None
    problems: tuple[str, ...] = ()


def comment_order(post: dict[str, Any]) -> tuple[datetime, int]:
    """Sort by GitHub creation instant and then by comment ID."""
    return timestamp(post["created_at"]), post["id"]


def structured_data(line: str, prefix: str) -> dict[str, Any]:
    """Read an object from a structured comment line."""
    try:
        data = json.loads(line.removeprefix(prefix))
    except (ValueError, RecursionError):
        return {}
    return data if isinstance(data, dict) else {}


def linked_deployments(github: cfr.GitHub, posts: list[dict[str, Any]]) -> set[str]:
    """Read trusted CFR markers and maintainer-authored correction links."""
    linked = set()
    for post in posts:
        body = post.get("body") or ""
        if (post.get("user") or {}).get("login") == "github-actions[bot]":
            linked.update(MARKER.findall(body))
        for line in body.splitlines():
            match = LINK.fullmatch(line)
            if match and github.maintainer(post):
                linked.add(match[1])
    return linked


def apply_timeline(claims: dict[str, Claim], data: dict[str, Any], linked: set[str]) -> None:
    """Apply only usable, source-backed degradation or restoration claims."""
    field = data.get("field")
    evidence = data.get("evidence")
    resolves = data.get("resolvesConflict")
    deploy = data.get("correctiveDeployId")
    recorded_time = data.get("timestamp")
    if (
        field not in ("degradation", "restoration")
        or data.get("source") not in ("monitoring", "maintainer-timeline")
        or not isinstance(recorded_time, str)
        or not isinstance(evidence, str)
        or not evidence.strip()
        or not isinstance(resolves, bool)
        or (
            "correctiveDeployId" in data
            and (field != "restoration" or not isinstance(deploy, str) or deploy not in linked)
        )
    ):
        return
    try:
        instant = timestamp(recorded_time)
    except (TypeError, ValueError, OverflowError):
        return
    claims[field].apply(instant, resolves=resolves)


def evaluate(github: cfr.GitHub, number: int, posts: list[dict[str, Any]]) -> Recovery | None:
    """Determine eligibility, restoration status, and duration for one issue."""
    comments = [
        post
        for post in posts[1:]
        if any(
            line.startswith((CONFIRMATION, TIMELINE))
            for line in (post.get("body") or "").splitlines()
        )
        and github.maintainer(post)
    ]
    confirmation: dict[str, Any] = {}
    timeline = []
    for post in sorted(comments, key=comment_order):
        for line in post["body"].splitlines():
            if line.startswith(CONFIRMATION):
                data = structured_data(line, CONFIRMATION)
                if isinstance(data.get("environment"), str) and all(
                    isinstance(data.get(flag), bool) for flag in FLAGS
                ):
                    confirmation = data
            elif line.startswith(TIMELINE):
                timeline.append(structured_data(line, TIMELINE))

    if confirmation.get("environment") != "production" or not all(
        confirmation[flag] for flag in FLAGS[:-1]
    ):
        return None
    if not confirmation["restored"]:
        return Recovery(number, "Unresolved")

    claims = {field: Claim() for field in ("degradation", "restoration")}
    linked = linked_deployments(github, posts)
    for data in timeline:
        apply_timeline(claims, data, linked)
    problems = tuple(
        f"Conflicting {field} timestamps" for field, claim in claims.items() if claim.disputed
    )
    start = claims["degradation"].time
    end = claims["restoration"].time
    if problems or start is None or end is None:
        return Recovery(number, "Missing timestamp", problems=problems)
    if end < start:
        return Recovery(number, "Missing timestamp", problems=("Restoration predates degradation",))
    return Recovery(number, "Completed", (end - start).total_seconds() / 60)


def load_recoveries(github: cfr.GitHub) -> list[Recovery]:
    """Verify the label and collect all qualifying issues."""
    try:
        label = github.object_request(f"labels/{LABEL}")
    except HTTPError:
        raise EvidenceError(f"Could not verify the {LABEL} label.") from None
    if label.get("name") != LABEL:
        raise EvidenceError(f"Could not verify the {LABEL} label.")

    recoveries = []
    for number, posts in cfr.issue_threads(github, labels=LABEL).items():
        recovery = evaluate(github, number, posts)
        if recovery is not None:
            recoveries.append(recovery)
    return recoveries


def duration(minutes: float) -> str:
    """Display elapsed minutes, including fractional minutes."""
    return f"{minutes:.9f}".rstrip("0").rstrip(".") + " minutes"


def heading(now: datetime) -> str:
    """Render the report title and UTC run time."""
    run_time = now.astimezone(UTC)
    return f"# DORA failed deployment recovery time\n\nRun time: {run_time:%F %T} UTC\n\n"


def build_report(github: cfr.GitHub, now: datetime) -> str:
    """Produce a complete report or an explicit incomplete-evidence summary."""
    try:
        recoveries = load_recoveries(github)
    except EvidenceError as error:
        return heading(now) + f"Incident evidence is incomplete. {error}\n"
    except (KeyError, TypeError, ValueError, OverflowError):
        return heading(now) + "Incident evidence is incomplete. Invalid GitHub incident data.\n"

    durations = [entry.minutes for entry in recoveries if entry.minutes is not None]
    unresolved = sum(entry.status == "Unresolved" for entry in recoveries)
    missing = sum(entry.status == "Missing timestamp" for entry in recoveries)
    lines = [
        f"Completed recoveries: {len(durations)}",
        f"Unresolved failures: {unresolved}",
        f"Restored failures with a missing timestamp: {missing}",
        (
            f"Median recovery duration: {duration(median(durations))}"
            if durations
            else "No completed recoveries with known timestamps."
        ),
    ]
    lines = ["\n\n".join(lines)]
    if recoveries:
        lines.extend(["", "| Incident | Status | Recovery duration |", "| --- | --- | --- |"])
    diagnostics: list[str] = []
    for entry in recoveries:
        number = entry.number
        link = f"[#{number}](https://github.com/{github.repo}/issues/{number})"
        elapsed = duration(entry.minutes) if entry.minutes is not None else ""
        lines.append(f"| {link} | {entry.status} | {elapsed} |")
        diagnostics.extend(f"- {link} — {problem}" for problem in entry.problems)
    if diagnostics:
        lines.extend(["", "## Timeline diagnostics", "", *diagnostics])
    return heading(now) + "\n".join(lines) + "\n"


def report_from_environment(now: datetime) -> str:
    """Render recovery evidence using the workflow repository and token."""
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GH_TOKEN")
    if repo and token:
        return build_report(cfr.GitHub(repo, token), now)
    return heading(now) + "Incident evidence is incomplete. GitHub configuration is missing.\n"


def main() -> int:
    """Read GitHub evidence and publish the report in the job summary."""
    started = os.getenv("DORA_REPORT_STARTED_AT")
    now = timestamp(started) if started else datetime.now(UTC)
    report = report_from_environment(now)
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
        output.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
