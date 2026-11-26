"""Report DORA change failure rate and reconcile production corrections."""

import json
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

if TYPE_CHECKING or __package__:
    from . import dora_evidence, dora_lead_time
else:
    import dora_evidence
    import dora_lead_time

EvidenceError = dora_evidence.EvidenceError
DAY = timedelta(days=1)
DEPLOY = r"dep-[A-Za-z0-9]+"
TRIGGERS = {
    "api",
    "blueprint_sync",
    "deploy_hook",
    "deployed_by_render",
    "manual",
    "other",
    "new_commit",
    "rollback",
    "service_resumed",
    "service_updated",
}
PROMOTIONS = Path("specs/devops/dora-change-failure-rate/promotions.json")
INCIDENT_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "specs/templates/devops/production-incident.md"
)
Arrival = tuple[dict[str, Any], datetime]
IssueThreads = dict[int, list[dict[str, Any]]]
ScanGap = tuple[datetime, str]


@dataclass(frozen=True)
class Incident:
    """Attribution evidence from a GitHub issue."""

    issue: int
    original: str | None
    started: datetime | None
    confirmed: bool
    latest_start: datetime | None = None
    kind: str | None = None
    link: str | None = None
    evidence_gap: str | None = None


@dataclass(frozen=True)
class Correction:
    """A corrective deployment and its explicit issue linkage."""

    deploy: str
    live: datetime
    kind: str
    links: tuple[str, ...]
    issue: int | None


class GitHub:
    """Read and write issues in the workflow repository."""

    def __init__(self, repo: str, token: str) -> None:
        """Use the workflow token for repository API requests."""
        self.repo = repo
        self.token = token
        self.base = f"https://api.github.com/repos/{repo}"
        self.permissions: dict[str, bool] = {}

    def pages(self, path: str, **params: str) -> list[dict[str, Any]]:
        """Read all pages in creation order."""
        result = []
        for page in range(1, 10001):
            query = urlencode(dict(params, per_page=100, page=page))
            rows, link = dora_evidence.request(f"{self.base}/{path}?{query}", self.token, "GitHub")
            result.extend(rows)
            if 'rel="next"' not in link:
                return result
        raise EvidenceError("GitHub issue pagination did not terminate.")

    def issues(self) -> list[dict[str, Any]]:
        """Include closed issues and exclude pull requests."""
        return [
            row
            for row in self.pages("issues", state="all", sort="created", direction="asc")
            if "pull_request" not in row
        ]

    def write(self, number: int | None, title: str, body: str) -> int:
        """Create the incident atomically or append an entry as an issue comment."""
        if number is None:
            path, payload = "issues", {"title": title, "body": body}
        else:
            path, payload = f"issues/{number}/comments", {"body": body}
        try:
            result = self.object_request(path, payload)
            return number if number is not None else result["number"]
        except (EvidenceError, HTTPError, KeyError):
            raise EvidenceError("GitHub incident write could not be verified.") from None

    def object_request(self, path: str, payload: dict[str, str] | None = None) -> dict[str, Any]:
        """Fetch a GitHub object and keep credentials on the API origin."""
        request = Request(
            f"{self.base}/{path}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with build_opener(dora_evidence.NoRedirect()).open(request, timeout=30) as response:
                result = json.load(response)
                if not isinstance(result, dict):
                    raise ValueError
                return result
        except HTTPError:
            raise
        except (OSError, ValueError):
            raise EvidenceError("GitHub evidence request failed.") from None

    def maintainer(self, post: dict[str, Any]) -> bool:
        """Verify that the author has write or admin permission on this repository."""
        user = post.get("user") or {}
        login = user.get("login", "")
        if user.get("type") != "User" or not re.fullmatch(r"[A-Za-z0-9-]+", login):
            return False
        if login not in self.permissions:
            try:
                data = self.object_request(f"collaborators/{login}/permission")
                self.permissions[login] = data["permission"] in {"write", "admin"}
            except HTTPError as error:
                if error.code != 404:
                    raise EvidenceError(
                        "GitHub maintainer permission evidence is unavailable."
                    ) from None
                self.permissions[login] = False
            except KeyError:
                raise EvidenceError("GitHub maintainer permission evidence is invalid.") from None
        return self.permissions[login]

    def comments(self, number: int) -> list[dict[str, Any]]:
        """Load the comments on one incident issue."""
        return self.pages(f"issues/{number}/comments")


def eligible_deployments(now: datetime, arrivals: Sequence[Arrival]) -> dict[str, datetime]:
    """Select original deployments within the reporting window."""
    return {
        row["id"]: live for row, live in arrivals if now - timedelta(days=31) < live <= now - DAY
    }


def could_count(record: Incident, deploy: str, live: datetime) -> bool:
    """Check whether attribution fits the original deployment's intervention window."""
    return (
        record.original in {None, deploy}
        and (record.latest_start is None or live <= record.latest_start)
        and (record.started is None or live <= record.started <= live + DAY)
    )


def counted_deployments(eligible: dict[str, datetime], incidents: Sequence[Incident]) -> set[str]:
    """Return distinct originals with verified qualifying attribution."""
    return {
        deploy
        for record in incidents
        if record.confirmed
        and record.started is not None
        and (deploy := record.original) is not None
        and deploy in eligible
        and could_count(record, deploy, eligible[deploy])
    }


def format_report(
    now: datetime,
    arrivals: Sequence[Arrival],
    incidents: Sequence[Incident],
    gaps: Sequence[str],
) -> str:
    """Calculate and format the results for either workflow trigger."""
    cutoff = now - DAY
    start = cutoff - timedelta(days=30)
    eligible = eligible_deployments(now, arrivals)
    counted = counted_deployments(eligible, incidents)
    missing = list(gaps)
    for record in incidents:
        if not record.confirmed and any(
            deploy not in counted and could_count(record, deploy, live)
            for deploy, live in eligible.items()
        ):
            missing.append(
                record.evidence_gap or f"Pending attribution on incident #{record.issue}."
            )
    rate = "Unavailable"
    suffix = ""
    if missing:
        rate += " (incomplete evidence)"
        suffix = " (confirmed so far)"
    elif eligible:
        rate = f"{100 * len(counted) / len(eligible):.2f}".rstrip("0").rstrip(".") + "%"
    return "\n".join(
        [
            "## DORA change failure rate",
            "",
            f"Window start (UTC): `{start.isoformat()}`",
            f"Window cutoff (UTC): `{cutoff.isoformat()}`",
            "",
            f"Requiring immediate intervention{suffix}: {len(counted)}",
            f"Total production deployments{suffix}: {len(eligible)}",
            f"Change failure rate: {rate}",
            "",
            *(f"- {gap}" for gap in dict.fromkeys(missing)),
            "",
        ]
    )


def pull_evidence(
    repo: str, token: str, now: datetime
) -> tuple[list[dora_lead_time.Pull], dict[int, str]]:
    """Load original PRs, promotions, and the hotfix labels and issue links."""
    pulls = []
    bodies = {}
    seen = set()
    try:
        for row in dora_lead_time.github_rows(repo, token):
            number = row["number"]
            if type(number) is not int or number < 1 or number in seen:
                raise ValueError
            seen.add(number)
            if row["merged_at"] is None:
                continue
            merged = dora_evidence.timestamp(row["merged_at"])
            base = row["base"]["ref"]
            if merged > now or base not in {"main", "staging"}:
                continue
            head = row["head"]
            promotion = (
                base == "main"
                and head["ref"] == "staging"
                and (head["repo"] or {}).get("full_name", "").casefold() == repo.casefold()
            )
            sha = dora_lead_time.revision(row["merge_commit_sha"])
            hotfix = not promotion and any(
                label["name"] == "production-hotfix" for label in row["labels"]
            )
            pulls.append(
                dora_lead_time.Pull(number, base, sha, merged, feature=hotfix, promotion=promotion)
            )
            if hotfix:
                bodies[number] = row["body"] or ""
    except (KeyError, TypeError, ValueError, AttributeError):
        raise EvidenceError("GitHub PR evidence is incomplete or invalid.") from None
    return pulls, bodies


def find_corrections(
    repo: str,
    service: str,
    arrivals: Sequence[Arrival],
    pulls: list[dora_lead_time.Pull],
    hotfix_bodies: dict[int, str],
    manifest: dict[str, list[int]],
    now: datetime,
) -> tuple[list[Correction], list[ScanGap]]:
    """Find independently verified corrections in live-time order."""
    corrections = []
    gaps = []
    shipped: set[int] = set()
    revisions: dict[str, set[int]] = {}
    last_unknown_shipment = None
    last_unknown_staging_shipment = None
    direct_hotfixes = [pull for pull in pulls if pull.base == "main" and pull.feature]
    pulls_by_number = {pull.number: pull for pull in pulls}
    end = now + timedelta(microseconds=1)
    for row, live in sorted(arrivals, key=lambda item: (item[1], item[0]["id"])):
        if live > now:
            continue
        deploy = row["id"]
        if row.get("trigger") == "rollback":
            link = f"https://dashboard.render.com/web/{service}/deploys/{deploy}"
            corrections.append(Correction(deploy, live, "rollback", (link,), None))
            continue
        shipment_known = False
        try:
            if row.get("trigger") not in TRIGGERS:
                raise EvidenceError("Render deployment trigger is missing or invalid.")
            revision = dora_lead_time.revision(row["commit"]["id"])
            production = dora_lead_time.Deploy(deploy, revision, live)
            if revision not in revisions:
                try:
                    revisions[revision] = {
                        pull.number
                        for pull, _ in dora_lead_time.resolve(pulls, [production], manifest, end)
                    }
                except EvidenceError as error:
                    if str(error) != "A deployed staging promotion requires reviewed provenance.":
                        raise
                    gaps.append((live, f"{deploy}: {error}"))
                    last_unknown_staging_shipment = live
            carried = revisions.get(revision)
            if carried is None:
                # A staging mapping can only add staging PRs. Main PR ancestry
                # remains usable even when a deployed revision contains that promotion.
                carried = {
                    pull.number
                    for pull, _ in dora_lead_time.resolve(direct_hotfixes, [production], {}, end)
                }
            if any(pulls_by_number[number].merged > live for number in carried):
                raise EvidenceError("Production deployment predates a hotfix PR merge.")
            candidates = carried - shipped
            shipped.update(carried)
            shipment_known = True
            newly_shipped = []
            for number in sorted(candidates):
                pull = pulls_by_number[number]
                if (last_unknown_shipment is not None and pull.merged <= last_unknown_shipment) or (
                    pull.base == "staging"
                    and last_unknown_staging_shipment is not None
                    and pull.merged <= last_unknown_staging_shipment
                ):
                    gaps.append(
                        (live, f"{deploy}: An earlier deployment may have shipped PR #{number}.")
                    )
                else:
                    newly_shipped.append(number)
            if newly_shipped:
                targets = set()
                for pr in newly_shipped:
                    for link in re.findall(
                        r"^Incident:[ \t]*(.*)$", hotfix_bodies[pr], re.MULTILINE | re.IGNORECASE
                    ):
                        match = re.fullmatch(
                            rf"(?:#|https://github\.com/{re.escape(repo)}/issues/)([1-9][0-9]*)",
                            link.strip(),
                            re.IGNORECASE,
                        )
                        if match is None:
                            raise EvidenceError(
                                f"Original hotfix PR #{pr} has invalid incident linkage."
                            )
                        targets.add(int(match[1]))
                if len(targets) > 1:
                    raise EvidenceError("Original hotfix PRs link different incident issues.")
                links = tuple(f"https://github.com/{repo}/pull/{pr}" for pr in newly_shipped)
                corrections.append(
                    Correction(deploy, live, "hotfix", links, next(iter(targets), None))
                )
        except (EvidenceError, KeyError, TypeError, ValueError) as error:
            detail = (
                str(error) if isinstance(error, EvidenceError) else "Invalid deployed revision."
            )
            gaps.append((live, f"{deploy}: {detail}"))
            if not shipment_known:
                last_unknown_shipment = live
    return corrections, gaps


def issue_threads(github: GitHub) -> IssueThreads:
    """Index issue bodies and comments, rejecting duplicate or truncated threads."""
    threads = {}
    for issue in github.issues():
        number = issue["number"]
        if number in threads:
            raise EvidenceError("GitHub returned duplicate issue evidence.")
        comments = github.comments(number) if issue.get("comments", 0) else []
        if len(comments) != issue.get("comments", 0):
            raise EvidenceError(f"GitHub comments on incident #{number} changed during collection.")
        threads[number] = [issue, *comments]
    return threads


def marker(service: str, deploy: str) -> str:
    """Return the durable corrective deployment key."""
    return f"<!-- dora-correction {service}/{deploy} -->"


def recorded_entries(threads: IssueThreads, service: str, deploy: str) -> list[tuple[int, str]]:
    """Find workflow-authored entries, including duplicate markers on one issue."""
    key = marker(service, deploy)
    return [
        (number, post.get("body") or "")
        for number, posts in threads.items()
        for post in posts
        if (post.get("user") or {}).get("login") == "github-actions[bot]"
        for _ in range((post.get("body") or "").count(key))
    ]


def recorded(threads: IssueThreads, service: str, deploy: str) -> list[int]:
    """Return the issue number for each recorded entry."""
    return [number for number, _ in recorded_entries(threads, service, deploy)]


def rollback_issue(github: GitHub, threads: IssueThreads, deploy: str) -> int | None:
    """Resolve an explicit rollback link declared on an incident issue."""
    matches = [
        number
        for number, posts in threads.items()
        if any(
            re.search(rf"^DORA rollback:[ \t]*{deploy}[ \t]*$", post.get("body") or "", re.M)
            and github.maintainer(post)
            for post in posts
        )
    ]
    if len(matches) > 1:
        raise EvidenceError(f"{deploy} is explicitly linked to multiple GitHub issues.")
    return next(iter(matches), None)


def record(
    github: GitHub, service: str, correction: Correction, threads: IssueThreads | None = None
) -> None:
    """Record a correction once while retaining existing issue text and attribution."""
    if threads is None:
        threads = issue_threads(github)
    matches = recorded(threads, service, correction.deploy)
    if matches:
        if len(matches) > 1:
            raise EvidenceError(f"{correction.deploy} has duplicate GitHub incident entries.")
        return
    issue = correction.issue
    if correction.kind == "rollback":
        issue = rollback_issue(github, threads, correction.deploy)
    if issue is not None and issue not in threads:
        raise EvidenceError(f"{correction.deploy} links unavailable incident #{issue}.")
    body = (
        INCIDENT_TEMPLATE.read_text(encoding="utf-8")
        .rstrip("\n")
        .format(
            marker=marker(service, correction.deploy),
            kind=correction.kind,
            live=correction.live.isoformat(),
            links="\n".join(f"- {link}" for link in correction.links),
            repo=github.repo,
        )
    )
    number = github.write(issue, f"Production {correction.kind} {correction.deploy}", body)
    threads.setdefault(number, []).append({"body": body, "user": {"login": "github-actions[bot]"}})


def valid_link(repo: str, service: str, kind: str, link: str) -> bool:
    """Validate the corrective action link for a confirmed intervention."""
    if kind == "rollback":
        return bool(
            re.fullmatch(
                rf"https://dashboard\.render\.com/web/{re.escape(service)}/deploys/{DEPLOY}", link
            )
        )
    return kind == "hotfix" and bool(
        re.fullmatch(
            rf"https://github\.com/{re.escape(repo)}/pull/[1-9][0-9]*", link, re.IGNORECASE
        )
    )


def attributions(
    github: GitHub, service: str, threads: IssueThreads
) -> tuple[list[Incident], set[tuple[int, str]], list[str]]:
    """Read attribution records without joining them to production evidence."""
    records, gaps = attribution_records(github, service, threads)
    return list(records.values()), set(records), gaps


def attribution_records(
    github: GitHub, service: str, threads: IssueThreads
) -> tuple[dict[tuple[int, str], Incident], list[str]]:
    """Read explicit maintainer attribution and keep malformed evidence visible."""
    incidents = {}
    gaps = []
    for number, posts in threads.items():
        for post in posts:
            body = post.get("body") or ""
            for line in body.splitlines():
                if not line.startswith("DORA attribution:") or not github.maintainer(post):
                    continue
                try:
                    data = json.loads(line.removeprefix("DORA attribution:"))
                    if data["service"] != service:
                        continue
                    corrective = data["corrective"]
                    original = data.get("original")
                    started = data.get("started")
                    confirmed = data["status"] == "confirmed"
                    if (
                        not re.fullmatch(DEPLOY, corrective)
                        or data["status"] not in {"confirmed", "pending"}
                        or (original is not None and not re.fullmatch(DEPLOY, original))
                        or (
                            confirmed
                            and not (
                                data.get("caused") is True
                                and original
                                and started
                                and valid_link(github.repo, service, data["type"], data["link"])
                                and (
                                    data["type"] != "rollback"
                                    or data["link"].endswith(f"/{corrective}")
                                )
                            )
                        )
                    ):
                        raise ValueError
                    at = dora_evidence.timestamp(started) if started is not None else None
                    incidents[number, corrective] = Incident(
                        number,
                        original,
                        at,
                        confirmed,
                        kind=data["type"] if confirmed else None,
                        link=data["link"] if confirmed else None,
                    )
                except (KeyError, AttributeError, TypeError, ValueError):
                    gaps.append(f"Invalid maintainer attribution on incident #{number}.")
    issues_by_deploy: dict[str, set[int]] = {}
    for number, corrective in incidents:
        issues_by_deploy.setdefault(corrective, set(recorded(threads, service, corrective))).add(
            number
        )
    for corrective, numbers in issues_by_deploy.items():
        if len(numbers) > 1:
            issues = ", ".join(f"#{number}" for number in sorted(numbers))
            gaps.append(f"{corrective} has attribution on multiple issues ({issues}).")
            for number in numbers:
                incidents.pop((number, corrective), None)
    return incidents, gaps


def configuration() -> tuple[GitHub, str, str, str]:
    """Read the shared production service configuration."""
    repo = os.getenv("GITHUB_REPOSITORY", "")
    service = os.getenv("DORA_RENDER_SERVICE_ID", "")
    first = os.getenv("DORA_RENDER_FIRST_DEPLOY_ID", "")
    github_token = os.getenv("GH_TOKEN", "")
    render_token = os.getenv("RENDER_API_KEY", "")
    if not (
        re.fullmatch(r"[\w.-]+/[\w.-]+", repo)
        and re.fullmatch(r"srv-[A-Za-z0-9]+", service)
        and re.fullmatch(rf"(?:{DEPLOY}|empty)", first)
        and github_token.strip()
        and render_token.strip()
    ):
        raise EvidenceError("Required GitHub or Render configuration is missing or invalid.")
    return GitHub(repo, github_token), service, render_token, first


def scan(
    github: GitHub, service: str, arrivals: Sequence[Arrival], now: datetime
) -> tuple[list[Correction], list[ScanGap]]:
    """Read provenance and identify missing evidence in the production history."""
    if not arrivals:
        return [], []
    try:
        pulls, bodies = pull_evidence(github.repo, github.token, now)
        manifest = dora_lead_time.promotion_manifest(PROMOTIONS)
    except EvidenceError as error:
        rollbacks = [arrival for arrival in arrivals if arrival[0].get("trigger") == "rollback"]
        corrections, _ = find_corrections(github.repo, service, rollbacks, [], {}, {}, now)
        gaps = [
            (live, f"{row['id']}: {error}")
            for row, live in arrivals
            if live <= now and row.get("trigger") != "rollback"
        ]
        return corrections, gaps
    return find_corrections(
        github.repo,
        service,
        arrivals,
        pulls,
        bodies,
        manifest,
        now,
    )


def load_report(now: datetime) -> tuple[list[Arrival], list[Incident], list[str]]:
    """Collect independent evidence and check the incident scan for missing entries."""
    github, service, render_token, first = configuration()
    arrivals: list[Arrival] = []
    incidents: list[Incident] = []
    gaps: list[str] = []
    try:
        arrivals = dora_evidence.fetch_production_arrivals(service, render_token, first)
    except EvidenceError as error:
        gaps.append(str(error))
    eligible = eligible_deployments(now, arrivals)
    if not eligible:
        return arrivals, incidents, gaps
    try:
        threads = issue_threads(github)
        attributed, incident_gaps = attribution_records(github, service, threads)
        gaps.extend(incident_gaps)
        corrections, scan_gaps = scan(github, service, arrivals, now)
        by_deploy = {correction.deploy: correction for correction in corrections}
        for (issue, deploy), attribution in attributed.items():
            correction = by_deploy.get(deploy)
            if attribution.confirmed:
                if correction is None:
                    problem = "production history cannot verify the corrective action went live"
                elif (
                    attribution.kind != correction.kind
                    or attribution.link not in correction.links
                    or not (
                        len(entries := recorded_entries(threads, service, deploy)) == 1
                        and entries[0][0] == issue
                        and f"- {attribution.link}" in entries[0][1].splitlines()
                    )
                ):
                    problem = "the corrective action does not match a unique recorded entry"
                else:
                    problem = None
                if problem:
                    attribution = replace(
                        attribution,
                        confirmed=False,
                        evidence_gap=f"Incident #{issue}, {deploy}: {problem}.",
                    )
            incidents.append(attribution)

        counted = counted_deployments(eligible, incidents)
        uncounted = [live for deploy, live in eligible.items() if deploy not in counted]
        gaps.extend(detail for live, detail in scan_gaps if any(at <= live for at in uncounted))
        for correction in corrections:
            if not any(live <= correction.live for live in uncounted):
                continue
            matches = recorded(threads, service, correction.deploy)
            if len(matches) != 1:
                gaps.append(f"{correction.deploy}: expected one GitHub incident entry.")
            elif (matches[0], correction.deploy) not in attributed:
                incidents.append(
                    Incident(matches[0], None, None, confirmed=False, latest_start=correction.live)
                )
    except EvidenceError as error:
        gaps.append(str(error))
    return arrivals, incidents, gaps


def main(mode: str, now: datetime | None = None) -> int:
    """Run the report or the scheduled writer."""
    if now is None:
        started = os.getenv("DORA_REPORT_STARTED_AT") if mode == "report" else None
        now = dora_evidence.timestamp(started) if started else datetime.now(UTC)
    if mode == "report":
        try:
            arrivals, incidents, gaps = load_report(now)
        except EvidenceError as error:
            arrivals, incidents, gaps = [], [], [str(error)]
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as output:
            output.write(format_report(now, arrivals, incidents, gaps))
        return 0
    try:
        github, service, token, first = configuration()
        arrivals = dora_evidence.fetch_production_arrivals(service, token, first)
        corrections, scan_gaps = scan(github, service, arrivals, now)
        threads = issue_threads(github) if corrections else {}
        for correction in corrections:
            record(github, service, correction, threads)
        if scan_gaps:
            raise EvidenceError(scan_gaps[0][1])
    except EvidenceError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    return 0


if __name__ == "__main__":
    if sys.argv[1:] not in (["report"], ["reconcile"]):
        sys.exit("Usage: dora_change_failure_rate.py {report|reconcile}")
    sys.exit(main(sys.argv[1]))
