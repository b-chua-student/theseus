"""Generate the feature PR merge-to-production lead time summary."""

import json
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

if TYPE_CHECKING or __package__:
    from . import dora_evidence
else:
    import dora_evidence

TITLE = "Feature PR merge-to-production lead time"
SHA = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class Pull:
    """GitHub evidence for a merged PR."""

    number: int
    base: str
    revision: str
    merged: datetime
    feature: bool
    promotion: bool


@dataclass(frozen=True)
class Deploy:
    """A successful production deployment."""

    deployment_id: str
    revision: str
    live: datetime


def revision(value: str) -> str:
    """Validate a full Git commit SHA."""
    if not SHA.fullmatch(value):
        raise ValueError
    return value


def github_rows(repo: str, token: str) -> Iterator[dict[str, Any]]:
    """Walk PRs in stable creation order using GitHub pagination."""
    endpoint = f"https://api.github.com/repos/{repo}/pulls"
    for page in range(1, 10001):
        query = urlencode(
            dict(state="all", sort="created", direction="asc", per_page=100, page=page)
        )
        rows, link = dora_evidence.request(f"{endpoint}?{query}", token, "GitHub")
        yield from rows
        if 'rel="next"' not in link:
            return
    raise dora_evidence.EvidenceError("GitHub PR pagination did not terminate.")


def fetch_pulls(repo: str, token: str, label: str, end: datetime) -> list[Pull]:
    """Read and classify original feature PRs and staging promotions."""
    pulls = []
    seen = set()
    try:
        for row in github_rows(repo, token):
            number = row["number"]
            if type(number) is not int or number < 1 or number in seen:
                raise ValueError
            seen.add(number)
            merged_value = row["merged_at"]
            if merged_value is None:
                continue
            merged = dora_evidence.timestamp(merged_value)
            base = row["base"]["ref"]
            if not isinstance(base, str) or not base:
                raise ValueError
            if merged >= end or base not in {"main", "staging"}:
                continue
            head = row["head"]
            promotion = (
                base == "main"
                and head["ref"] == "staging"
                and (head["repo"] or {}).get("full_name", "").casefold() == repo.casefold()
            )
            labels = row["labels"]
            if not isinstance(labels, list) or any(
                not isinstance(item["name"], str) for item in labels
            ):
                raise ValueError
            feature = not promotion and any(
                item["name"].casefold() == label.casefold() for item in labels
            )
            pulls.append(
                Pull(number, base, revision(row["merge_commit_sha"]), merged, feature, promotion)
            )
    except (KeyError, TypeError, ValueError, AttributeError):
        raise dora_evidence.EvidenceError("GitHub PR evidence is incomplete or invalid.") from None
    return pulls


def fetch_deploys(service: str, token: str, first_id: str) -> list[Deploy]:
    """Add Git revision evidence for the lead time report."""
    arrivals = dora_evidence.fetch_production_arrivals(service, token, first_id)
    try:
        return [Deploy(row["id"], revision(row["commit"]["id"]), live) for row, live in arrivals]
    except (KeyError, TypeError, ValueError):
        raise dora_evidence.EvidenceError(
            "Render deployment evidence is incomplete or invalid."
        ) from None


def git(*args: str) -> list[str]:
    """Read local commit history with suppressed command diagnostics."""
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", *args],
            capture_output=True,
            check=True,
            text=True,
            timeout=60,
        )
        return result.stdout.splitlines()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise dora_evidence.EvidenceError("Required Git revision history is unavailable.") from None


def promotion_manifest(
    path: Path = Path("specs/devops/dora-change-lead-time/promotions.json"),
) -> dict[str, list[int]]:
    """Load maintainer-reviewed mappings of promotion revisions to original staging PRs."""
    if not path.exists():
        return {}
    try:
        entries = json.loads(path.read_text())
        for sha, numbers in entries.items():
            revision(sha)
            if (
                not isinstance(numbers, list)
                or any(type(number) is not int or number < 1 for number in numbers)
                or len(numbers) != len(set(numbers))
            ):
                raise ValueError
    except (OSError, ValueError, TypeError, AttributeError):
        raise dora_evidence.EvidenceError("Promotion evidence file is invalid.") from None
    return entries


def resolve(
    pulls: list[Pull],
    deploys: list[Deploy],
    manifest: dict[str, list[int]],
    end: datetime,
) -> Iterator[tuple[Pull, Deploy]]:
    """Resolve original feature PRs by reachability and reviewed promotion evidence."""
    if git("rev-parse", "--is-shallow-repository") != ["false"]:
        raise dora_evidence.EvidenceError("Complete Git revision history is required.")
    features = {pull.number: pull for pull in pulls if pull.feature}
    promotion_pulls = [
        pull
        for pull in pulls
        if pull.promotion or (pull.base == "main" and pull.revision in manifest)
    ]
    promotions = {pull.revision: pull for pull in promotion_pulls}
    if len(promotions) != len(promotion_pulls):
        raise dora_evidence.EvidenceError("GitHub promotion revisions are ambiguous.")
    if manifest.keys() - promotions.keys():
        raise dora_evidence.EvidenceError("Promotion evidence does not match a merged main PR.")
    cache: dict[str, tuple[set[int], set[str]]] = {}
    for deploy in deploys:
        if deploy.live >= end:
            continue
        if deploy.revision not in cache:
            reachable = {
                sha: parents
                for sha, *parents in (
                    line.split() for line in git("rev-list", "--parents", deploy.revision)
                )
            }
            numbers = {
                number
                for number, pull in features.items()
                if pull.revision in reachable and pull.revision not in promotions
            }
            carried_promotions = promotions.keys() & reachable
            for sha in carried_promotions:
                promotion = promotions[sha]
                if sha in manifest:
                    for number in manifest[sha]:
                        original = features.get(number)
                        if (
                            original is None
                            or original.base != "staging"
                            or original.merged > promotion.merged
                        ):
                            raise dora_evidence.EvidenceError(
                                "Promotion evidence references an invalid PR."
                            )
                        numbers.add(number)
                elif len(reachable[sha]) != 2:
                    raise dora_evidence.EvidenceError(
                        "A deployed staging promotion requires reviewed provenance."
                    )
            cache[deploy.revision] = numbers, carried_promotions
        numbers, carried_promotions = cache[deploy.revision]
        for sha in carried_promotions:
            if promotions[sha].merged > deploy.live:
                raise dora_evidence.EvidenceError("Production deployment predates its promotion.")
        for number in sorted(numbers):
            yield features[number], deploy


def calculate(
    traces: Iterator[tuple[Pull, Deploy]],
    end: datetime,
) -> tuple[datetime, list[tuple[Pull, Deploy]], float | None]:
    """Find each PR's first live deployment and compute the window median."""
    start = end - timedelta(days=30)
    first: dict[int, tuple[Pull, Deploy]] = {}
    for pull, deploy in traces:
        if deploy.live >= end:
            continue
        if deploy.live < pull.merged:
            raise dora_evidence.EvidenceError("Production deployment predates a feature PR merge.")
        earlier = first.get(pull.number)
        if earlier is None or (deploy.live, deploy.deployment_id) < (
            earlier[1].live,
            earlier[1].deployment_id,
        ):
            first[pull.number] = pull, deploy
    included = [trace for _, trace in sorted(first.items()) if start <= trace[1].live < end]
    hours = [(deploy.live - pull.merged).total_seconds() / 3600 for pull, deploy in included]
    return start, included, median(hours) if hours else None


def format_report(
    start: datetime,
    end: datetime,
    included: list[tuple[Pull, Deploy]],
    hours: float | None,
) -> str:
    """Format the aggregate and the evidence needed for maintainer verification."""
    value = "Unavailable" if hours is None else f"{hours:.2f}"
    lines = [
        f"## {TITLE}",
        "",
        f"Window (UTC): `{start.isoformat()}` to `{end.isoformat()}`",
        "",
        f"Included feature PR count: {len(included)}",
        "",
        f"Median lead time (hours): {value}",
        "",
    ]
    if included:
        lines.extend(
            [
                "<details><summary>PR-to-deployment evidence</summary>",
                "",
                "| PR | Merged (UTC) | Render deploy | Commit | First live (UTC) |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for pull, deploy in included:
            lines.append(
                f"| #{pull.number} | {pull.merged.isoformat()} | {deploy.deployment_id} "
                f"| `{deploy.revision}` | {deploy.live.isoformat()} |"
            )
        lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def main() -> int:
    """Publish a complete summary or emit a fixed error diagnostic."""
    end = datetime.now(UTC)
    try:
        repo = os.environ["GITHUB_REPOSITORY"]
        github_token = os.environ["GH_TOKEN"]
        service = os.environ["DORA_RENDER_SERVICE_ID"]
        render_token = os.environ["RENDER_API_KEY"]
        first_id = os.environ["DORA_RENDER_FIRST_DEPLOY_ID"]
        label = os.environ["DORA_FEATURE_LABEL"]
        summary = Path(os.environ["GITHUB_STEP_SUMMARY"])
        if not (
            re.fullmatch(r"[\w.-]+/[\w.-]+", repo)
            and re.fullmatch(r"srv-[A-Za-z0-9]+", service)
            and re.fullmatch(r"(?:dep-[A-Za-z0-9]+|empty)", first_id)
            and all(value.strip() for value in (github_token, render_token, label))
        ):
            raise dora_evidence.EvidenceError(
                "Required reporting configuration is missing or invalid."
            )
        deploys = fetch_deploys(service, render_token, first_id)
        pulls = fetch_pulls(repo, github_token, label, end)
        traces = resolve(pulls, deploys, promotion_manifest(), end)
        start, included, hours = calculate(traces, end)
        report = format_report(start, end, included, hours)
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=summary.parent, delete=False
        ) as output:
            temporary = Path(output.name)
            try:
                output.write(report)
                output.close()
                temporary.replace(summary)
            finally:
                temporary.unlink(missing_ok=True)
    except dora_evidence.EvidenceError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    except KeyError:
        sys.stderr.write("Required reporting configuration is missing.\n")
        return 1
    except Exception:
        sys.stderr.write("Unable to generate the lead time report.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
