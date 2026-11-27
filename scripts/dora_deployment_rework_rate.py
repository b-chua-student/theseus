"""Publish the DORA deployment rework rate from production and incident evidence."""

import os
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING or __package__:
    from . import dora_change_failure_rate as cfr
    from . import dora_evidence
else:
    import dora_change_failure_rate as cfr
    import dora_evidence

EvidenceError = dora_evidence.EvidenceError
CORRECTION = re.compile(rf"<!-- dora-correction (srv-[A-Za-z0-9]+)/({cfr.DEPLOY}) -->")
COMMAND = re.compile(rf"/dora rework[ \t]+(srv-[A-Za-z0-9]+)[ \t]+({cfr.DEPLOY})[ \t]*")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")


@dataclass
class IncidentEvidence:
    """Keep verified confirmations and the scope of unavailable evidence."""

    confirmed: set[str] = field(default_factory=set)
    scoped_gaps: set[str] = field(default_factory=set)
    unknown_gap: bool = False

    def affected(self, deployments: set[str]) -> set[str]:
        """Return deployments whose rework status can still change."""
        candidates = deployments if self.unknown_gap else deployments & self.scoped_gaps
        return candidates - self.confirmed


def production_window(service: str, token: str, first: str, end: datetime) -> set[str]:
    """Select verified production arrivals in the half-open reporting window."""
    start = end - timedelta(days=30)
    return {
        row["id"]
        for row, live in dora_evidence.fetch_production_arrivals(service, token, first)
        if start <= live < end
    }


def commands(body: str, service: str) -> Iterator[str]:
    """Read standalone rework commands, skipping fenced examples."""
    fence = ""
    for line in body.splitlines():
        if match := FENCE.fullmatch(line):
            delimiter, suffix = match.groups()
            if not fence:
                fence = delimiter
            elif delimiter.startswith(fence) and not suffix.strip():
                fence = ""
        elif not fence and (match := COMMAND.fullmatch(line)) and match[1] == service:
            yield match[2]


def correction_scope(posts: list[dict[str, Any]], service: str) -> set[str]:
    """Find explicit corrective deployment markers for this service."""
    return {
        deploy
        for post in posts
        for marked_service, deploy in CORRECTION.findall(post.get("body") or "")
        if marked_service == service
    }


def production_incident(issue: dict[str, Any]) -> bool:
    """Recognize issues from the incident template, recovery records, and reconciled issues."""
    return (
        issue["title"].casefold().startswith("[production incident]")
        or any(label["name"] == "dora-recovery-incident" for label in issue.get("labels", []))
        or (
            (issue.get("user") or {}).get("login") == "github-actions[bot]"
            and bool(CORRECTION.search(issue.get("body") or ""))
        )
    )


def read_incident(
    github: cfr.GitHub,
    issue: dict[str, Any],
    service: str,
    deployments: set[str],
    evidence: IncidentEvidence,
) -> None:
    """Keep readable comments even when part of the thread is unavailable."""
    number, expected = issue["number"], issue["comments"]
    if type(number) is not int or number < 1 or type(expected) is not int or expected < 0:
        raise EvidenceError("GitHub incident metadata is invalid.")
    if not expected:
        return

    posts = [issue]
    incomplete = False
    try:
        for post in github.iter_rows(f"issues/{number}/comments"):
            if not isinstance(post, dict) or not isinstance(post.get("body"), str):
                incomplete = True
                continue
            posts.append(post)
            targets = (set(commands(post["body"], service)) & deployments) - evidence.confirmed
            if targets:
                try:
                    if github.maintainer(post):
                        evidence.confirmed.update(targets)
                except (EvidenceError, AttributeError, TypeError):
                    evidence.scoped_gaps.update(targets)
    except EvidenceError:
        incomplete = True

    if incomplete or len(posts) - 1 < expected:
        scope = correction_scope(posts, service)
        evidence.scoped_gaps.update(scope)
        evidence.unknown_gap = True


def read_incidents(service: str, deployments: set[str]) -> IncidentEvidence:
    """Collect rework evidence from production incident issues, including closed ones."""
    repo = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GH_TOKEN", "")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) or not token.strip():
        return IncidentEvidence(unknown_gap=True)

    github = cfr.GitHub(repo, token)
    evidence = IncidentEvidence()
    try:
        for issue in github.iter_rows("issues", state="all", sort="created", direction="asc"):
            try:
                if "pull_request" not in issue and production_incident(issue):
                    read_incident(github, issue, service, deployments, evidence)
            except (EvidenceError, KeyError, AttributeError, TypeError):
                evidence.unknown_gap = True
    except EvidenceError:
        evidence.unknown_gap = True
    return evidence


def format_result(deployments: set[str], evidence: IncidentEvidence) -> str:
    """Report the confirmed counts and the applicable rate or evidence status."""
    total = len(deployments)
    confirmed = len(evidence.confirmed)
    if affected := evidence.affected(deployments):
        return (
            f"Production deployments: {total}\n"
            f"Confirmed rework deployments: {confirmed}\n"
            f"Deployments affected by the evidence gap: {len(affected)}\n"
            "Status: Incomplete evidence\n"
        )
    if total:
        rate = f"{100 * confirmed / total:.2f}".rstrip("0").rstrip(".") + "%"
    else:
        rate = "N/A — no production deployments"
    return (
        f"Rework deployments: {confirmed}\n"
        f"Production deployments: {total}\n"
        f"Deployment rework rate: {rate}\n"
    )


def main() -> int:
    """Use the captured UTC report start and append the result to the job summary."""
    try:
        end = dora_evidence.timestamp(os.environ["DORA_REPORT_STARTED_AT"])
    except (KeyError, ValueError):
        sys.stderr.write("The UTC report start is missing or invalid.\n")
        return 1
    start = end - timedelta(days=30)
    service = os.getenv("DORA_RENDER_SERVICE_ID", "")
    token = os.getenv("RENDER_API_KEY", "")
    first = os.getenv("DORA_RENDER_FIRST_DEPLOY_ID", "")
    try:
        if not (
            re.fullmatch(r"srv-[A-Za-z0-9]+", service)
            and re.fullmatch(rf"(?:{cfr.DEPLOY}|empty)", first)
            and token.strip()
        ):
            raise EvidenceError("Required Render configuration is missing or invalid.")
        deployments = production_window(service, token, first, end)
    except EvidenceError as error:
        result = f"Production deployments: Unverified\nStatus: Incomplete evidence\n\n- {error}\n"
    else:
        evidence = read_incidents(service, deployments) if deployments else IncidentEvidence()
        result = format_result(deployments, evidence)

    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
        output.write(
            "## DORA deployment rework rate\n\n"
            f"Window start (UTC): `{start.isoformat()}`\n"
            f"Window end (UTC, exclusive): `{end.isoformat()}`\n\n"
            f"{result}\n"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
