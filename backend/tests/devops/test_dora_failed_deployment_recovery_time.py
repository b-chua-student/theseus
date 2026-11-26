import importlib
import json
from datetime import UTC, datetime
from http.client import HTTPMessage
from types import ModuleType
from urllib.error import HTTPError

import pytest
from scripts import dora_change_failure_rate as cfr

from tests.devops.test_dora_change_failure_rate import Issues

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)
START = "2026-10-01T10:00:00Z"
LABEL = "dora-recovery-incident"
EMPTY = "No completed recoveries with known timestamps."


@pytest.fixture
def recovery() -> ModuleType:
    return importlib.import_module("scripts.dora_failed_deployment_recovery_time")


class Repository(Issues):
    def __init__(self) -> None:
        super().__init__()
        self.label_error: int | None = None
        self.load_error = False

    def object_request(self, path, payload=None) -> dict:
        assert path == f"labels/{LABEL}"
        if self.label_error:
            raise HTTPError(path, self.label_error, "", HTTPMessage(), None)
        return {"name": LABEL}

    def pages(self, path, **params: str) -> list[dict]:
        assert path == "issues"
        assert params["state"] == "all"
        assert params["labels"] == LABEL
        if self.load_error:
            raise cfr.EvidenceError("Issue collection failed.")
        return [row for row in self.rows.values() if LABEL in row.get("labels", [])]

    @staticmethod
    def maintainer(post) -> bool:
        login = (post.get("user") or {}).get("login")
        return login != "github-actions[bot]" and Issues.maintainer(post)

    def comment(self, number, body, **metadata: object) -> None:
        posts = self.posts.setdefault(number, [])
        posts.append(
            {
                "body": body,
                "id": len(posts) + 1,
                "created_at": "2026-11-01T12:00:00Z",
                **metadata,
            }
        )
        self.rows[number]["comments"] = len(posts)

    def confirm(self, number, **fields: object) -> None:
        data = dict(
            environment="production",
            degraded=True,
            deploymentCaused=True,
            immediateIntervention=True,
            restored=True,
        )
        self.comment(number, "DORA recovery: " + json.dumps(data | fields))

    def timeline(self, number, field, timestamp, **fields: object) -> None:
        data = dict(
            field=field,
            timestamp=timestamp,
            source="monitoring",
            evidence="Production monitoring",
            resolvesConflict=False,
        )
        self.comment(number, "DORA recovery timeline: " + json.dumps(data | fields))

    def incident(self, number, *, start=START, end=None, **fields: object) -> None:
        self.rows[number] = {"number": number, "labels": [LABEL]}
        self.confirm(number, **fields)
        if start:
            self.timeline(number, "degradation", start)
        if end:
            self.timeline(number, "restoration", end)


def counts(report, completed, unresolved, missing) -> None:
    assert f"Completed recoveries: {completed}\n" in report
    assert f"Unresolved failures: {unresolved}\n" in report
    assert f"Restored failures with a missing timestamp: {missing}\n" in report


def entry(report, number, status, duration="") -> None:
    link = f"[#{number}](https://github.com/owner/repo/issues/{number})"
    assert f"{link} | {status} | {duration} |" in report


@pytest.mark.parametrize(
    ("live", "end", "duration"),
    [
        ("10:45", "10:45", 45),
        ("10:20", "10:30", 30),
        (None, "10:30", 30),
    ],
    ids=["S-050", "S-049", "S-054"],
)
def test_confirmed_recovery(recovery, live, end, duration) -> None:
    repo = Repository()
    repo.incident(1)
    if live:
        cfr.record(
            repo,
            "srv-prod",
            cfr.Correction(
                "dep-hotfix",
                datetime.fromisoformat(f"2026-10-01T{live}:00Z"),
                "hotfix",
                (),
                1,
            ),
        )
    details = {"correctiveDeployId": "dep-hotfix"} if live == end else {}
    repo.timeline(1, "restoration", f"2026-10-01T{end}:00Z", **details)
    entry(recovery.build_report(repo, NOW), 1, "Completed", f"{duration} minutes")


@pytest.mark.parametrize("late", [False, True], ids=["S-055", "S-063"])
def test_links_preserve_incident_and_cfr_evidence(recovery, late) -> None:
    repo = Repository()
    repo.incident(1, end="2026-10-01T10:35:00Z")
    original = list(repo.posts[1])
    for deploy in ("dep-first", "dep-second"):
        if late and deploy == "dep-first":
            continue
        correction = cfr.Correction(deploy, NOW, "hotfix", (), None if late else 1)
        cfr.record(repo, "srv-prod", correction)
        if late:
            before = repo.rows[99].copy()
            repo.comment(1, f"DORA corrective deploy: {deploy}\nCorrection evidence: #99")
            assert repo.rows[99] == before
        assert cfr.recorded(cfr.issue_threads(repo), "srv-prod", deploy) == [99 if late else 1]
    assert repo.posts[1][: len(original)] == original
    if late:
        assert "DORA corrective deploy: dep-second" in repo.posts[1][-1]["body"]
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Completed", "35 minutes")
    assert "[#99]" not in report
    counts(report, 1, 0, 0)
    assert "Median recovery duration: 35 minutes" in report


@pytest.mark.parametrize("mixed", [True, False], ids=["S-046", "S-057"])
def test_median(recovery, mixed) -> None:
    repo = Repository()
    repo.incident(1, end="2026-10-01T10:15:00Z")
    repo.incident(2, end="2026-10-01T10:45:00Z")
    if mixed:
        repo.incident(3, end="2026-10-01T12:00:00Z")
        repo.incident(4, restored=False)
        repo.incident(5, restored=False)
        repo.incident(6)
    report = recovery.build_report(repo, NOW)
    counts(report, 3 if mixed else 2, 2 if mixed else 0, 1 if mixed else 0)
    assert f"Median recovery duration: {45 if mixed else 30} minutes" in report


@pytest.mark.parametrize(
    "fields",
    [
        {"environment": "staging"},
        {"deploymentCaused": False},
        {"immediateIntervention": False},
        {"degraded": False},
    ],
    ids=["S-051-staging", "S-051-unattributed", "S-051-no-intervention", "S-048"],
)
def test_nonqualifying_incident(recovery, fields) -> None:
    repo = Repository()
    for number, confirmation in [(1, {}), (2, fields)]:
        repo.incident(number, end="2026-10-01T10:45:00Z", **confirmation)
    report = recovery.build_report(repo, NOW)
    assert "[#2]" not in report
    counts(report, 1, 0, 0)
    assert "Median recovery duration: 45 minutes" in report


@pytest.mark.parametrize("start", [START, None], ids=["S-052-S-047", "S-058"])
def test_unresolved_before_correction(recovery, start) -> None:
    repo = Repository()
    repo.incident(1, start=start, restored=False)
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Unresolved")
    counts(report, 0, 1, 0)
    assert EMPTY in report


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (None, START),
        (START, None),
        (None, None),
    ],
    ids=["S-053-no-start", "S-053-no-end", "S-053-neither"],
)
def test_missing_timestamp(recovery, start, end) -> None:
    repo = Repository()
    repo.incident(1, start=start, end=end)
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Missing timestamp")
    counts(report, 0, 0, 1)


def test_s056_empty(recovery) -> None:
    report = recovery.build_report(Repository(), NOW)
    assert "/issues/" not in report
    counts(report, 0, 0, 0)
    assert EMPTY in report


def test_s059_manual_refresh_with_live_evidence(recovery, monkeypatch, tmp_path) -> None:
    repo = Repository()
    repo.incident(1)
    repo.comment(1, "DORA corrective deploy: dep-hotfix")
    repo.timeline(1, "restoration", "2026-10-01T10:45:00Z", correctiveDeployId="dep-hotfix")
    repo.incident(2, start="2026-11-27T11:00:00Z", restored=False)
    for name in (
        "RENDER_API_KEY",
        "DORA_RENDER_SERVICE_ID",
        "DORA_RENDER_FIRST_DEPLOY_ID",
        "DORA_FEATURE_LABEL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GITHUB_REPOSITORY", repo.repo)
    monkeypatch.setenv("GH_TOKEN", repo.token)
    monkeypatch.setenv("DORA_REPORT_STARTED_AT", NOW.isoformat())
    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    def github(repository, token) -> Repository:
        assert (repository, token) == (repo.repo, repo.token)
        return repo

    monkeypatch.setattr(cfr, "GitHub", github)
    assert recovery.main() == 0
    report = summary.read_text()
    entry(report, 1, "Completed", "45 minutes")
    entry(report, 2, "Unresolved")
    assert "2026-11-27 12:00:00 UTC" in report


@pytest.mark.parametrize(
    ("field", "time", "problem"),
    [
        ("degradation", "10:01", "Conflicting degradation timestamps"),
        ("restoration", "10:46", "Conflicting restoration timestamps"),
        ("restoration", "09:59", "Restoration predates degradation"),
    ],
    ids=["S-060-degradation", "S-060-restoration", "S-060-order"],
)
def test_unusable_timeline(recovery, field, time, problem) -> None:
    repo = Repository()
    repo.incident(1, end=None if time == "09:59" else "2026-10-01T10:45:00Z")
    repo.timeline(1, field, f"2026-10-01T{time}:00Z")
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Missing timestamp")
    counts(report, 0, 0, 1)
    assert f"/issues/1) — {problem}" in report


def test_s061_latest_resolution_wins(recovery) -> None:
    repo = Repository()
    repo.incident(1, end="2026-10-01T10:15:00Z")
    for time, resolves in [("10:20", False), ("10:30", True), ("10:45", True)]:
        repo.timeline(1, "restoration", f"2026-10-01T{time}:00Z", resolvesConflict=resolves)
    repo.posts[1].reverse()
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Completed", "45 minutes")
    counts(report, 1, 0, 0)
    assert "Median recovery duration: 45 minutes" in report


@pytest.mark.parametrize("failure", ["list", 404, 403], ids=["S-062", "label-404", "label-403"])
def test_incomplete_evidence(recovery, failure) -> None:
    repo = Repository()
    if failure == "list":
        repo.load_error = True
    else:
        repo.label_error = failure
    report = recovery.build_report(repo, NOW)
    assert "Incident evidence is incomplete" in report
    assert "Completed recoveries:" not in report
    assert EMPTY not in report


def test_cfr_issue_before_and_after_confirmation(recovery) -> None:
    repo = Repository()
    deploy = "dep-hotfix"
    cfr.record(repo, "srv-prod", cfr.Correction(deploy, NOW, "hotfix", (), None))
    repo.rows[99]["labels"] = [LABEL]
    counts(recovery.build_report(repo, NOW), 0, 0, 0)
    repo.confirm(99)
    repo.timeline(99, "degradation", START)
    repo.timeline(99, "restoration", "2026-10-01T10:45:00Z", correctiveDeployId=deploy)
    report = recovery.build_report(repo, NOW)
    entry(report, 99, "Completed", "45 minutes")
    counts(report, 1, 0, 0)
    assert cfr.recorded(cfr.issue_threads(repo), "srv-prod", deploy) == [99]


def test_unlinked_live_claim_cannot_resolve_conflict(recovery) -> None:
    repo = Repository()
    repo.incident(1, end="2026-10-01T10:15:00Z")
    repo.timeline(1, "restoration", "2026-10-01T10:20:00Z")
    repo.timeline(
        1,
        "restoration",
        "2026-10-01T10:45:00Z",
        resolvesConflict=True,
        correctiveDeployId="dep-unlinked",
    )
    report = recovery.build_report(repo, NOW)
    entry(report, 1, "Missing timestamp")
    assert "Conflicting restoration timestamps" in report
