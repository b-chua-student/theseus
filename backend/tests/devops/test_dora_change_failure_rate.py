import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from scripts import dora_change_failure_rate as cfr

NOW = datetime(2025, 11, 25, 12, tzinfo=UTC)
CUTOFF = NOW - timedelta(days=1)
START = CUTOFF - timedelta(days=30)
REPO = "owner/repo"
SERVICE = "srv-prod"
SHA = "a" * 40


def arrival(number, at=CUTOFF, **fields: object) -> cfr.Arrival:
    return ({"id": f"dep-{number}", **fields}, at)


def incident(number, at, kind="rollback", *, confirmed=True, issue=5) -> cfr.Incident:
    data = {
        "service": SERVICE,
        "corrective": "dep-correction",
        "original": f"dep-{number}" if number else None,
        "started": at.isoformat() if at else None,
        "status": "confirmed" if confirmed else "pending",
        "type": kind,
        "caused": confirmed,
        "link": (
            f"https://dashboard.render.com/web/{SERVICE}/deploys/dep-correction"
            if kind == "rollback"
            else f"https://github.com/{REPO}/pull/7"
        ),
    }
    threads = {issue: [{"body": f"DORA attribution: {json.dumps(data)}"}]}
    records, _, gaps = cfr.attributions(Issues(), SERVICE, threads)
    assert not gaps
    return records[0]


def report(arrivals, incidents=(), gaps=()) -> str:
    return cfr.format_report(NOW, arrivals, incidents, gaps)


@pytest.mark.parametrize(
    ("records", "count", "rate"),
    [
        ([(1, "rollback"), (2, "hotfix"), (9, "rollback")], 2, "50%"),
        ([(1, "rollback"), (1, "hotfix")], 1, "25%"),
        ([], 0, "0%"),
    ],
    ids=["S-028", "S-029", "S-030"],
)
def test_rate(records, count, rate) -> None:
    result = report(
        [arrival(i) for i in range(1, 5)],
        [incident(number, CUTOFF, kind) for number, kind in records],
    )
    assert f"Requiring immediate intervention: {count}" in result
    assert "Total production deployments: 4" in result
    assert f"Change failure rate: {rate}" in result


def test_s033_intervention_boundary() -> None:
    result = report(
        [arrival(1, CUTOFF), arrival(2, CUTOFF - timedelta(hours=1))],
        [incident(1, NOW), incident(2, NOW, "hotfix")],
    )
    assert "Requiring immediate intervention: 1" in result


def test_s034_empty() -> None:
    result = report([])
    assert "Requiring immediate intervention: 0" in result
    assert "Total production deployments: 0" in result
    assert "Change failure rate: Unavailable" in result


@pytest.mark.parametrize("pending", [False, True], ids=["history", "pending-issue"])
def test_s035_incomplete(pending) -> None:
    result = report(
        [arrival(1), arrival(2)],
        [
            incident(1, CUTOFF),
            *([incident(None, None, confirmed=False, issue=91)] if pending else []),
        ],
        [] if pending else ["Render history is unavailable."],
    )
    assert "Unavailable (incomplete evidence)" in result
    assert "confirmed so far" in result
    assert ("#91" if pending else "Render history is unavailable.") in result


def workflow() -> dict[str, Any]:
    path = Path(".github/workflows/dora-change-failure-rate.yml")
    return yaml.load(path.read_text(), Loader=yaml.BaseLoader)


def test_s031_manual_trigger() -> None:
    assert "workflow_dispatch" in workflow()["on"]


def test_s032_merged_main_trigger() -> None:
    config = workflow()
    assert config["on"]["pull_request_target"] == {"types": ["closed"], "branches": ["main"]}
    assert "github.event.pull_request.merged" in config["jobs"]["report"]["if"]


@pytest.mark.parametrize("trigger", ["workflow_dispatch", "pull_request_target"])
@pytest.mark.parametrize(("hour", "count", "rate"), [(12, 1, "50%"), (13, 0, "0%")])
def test_s036_same_window(trigger, hour, count, rate, monkeypatch, tmp_path) -> None:
    assert trigger in workflow()["on"]
    assert any(
        step.get("run") == "python scripts/dora_change_failure_rate.py report"
        for step in workflow()["jobs"]["report"]["steps"]
    )
    deployment = CUTOFF.replace(hour=hour)
    arrivals = [arrival(h, CUTOFF.replace(hour=h)) for h in (11, 12, 13)]
    monkeypatch.setattr(
        cfr,
        "load_report",
        lambda *_: (arrivals, [incident(hour, deployment + timedelta(hours=1))], []),
    )
    for name, value in {
        "GITHUB_EVENT_NAME": trigger,
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        "GITHUB_REPOSITORY": REPO,
        "GH_TOKEN": "github",
        "RENDER_API_KEY": "render",
        "DORA_RENDER_SERVICE_ID": SERVICE,
        "DORA_RENDER_FIRST_DEPLOY_ID": "dep-11",
    }.items():
        monkeypatch.setenv(name, value)
    assert cfr.main("report", NOW) == 0
    result = (tmp_path / "summary").read_text()
    assert START.isoformat() in result
    assert CUTOFF.isoformat() in result
    assert f"Requiring immediate intervention: {count}" in result
    assert "Total production deployments: 2" in result
    assert f"Change failure rate: {rate}" in result


class Issues(cfr.GitHub):
    def __init__(self, *, linked=False) -> None:
        super().__init__(REPO, "fixture-token")
        self.rows: dict[int, dict[str, Any]] = (
            {12: {"number": 12, "body": "Existing incident"}} if linked else {}
        )
        self.posts: dict[int, list[dict[str, Any]]] = {}

    @staticmethod
    def maintainer(post) -> bool:
        return post.get("permission", "write") in {"write", "admin"}

    def comments(self, number) -> list[dict[str, Any]]:
        return self.posts[number]

    def issues(self, **filters: str) -> list[dict[str, Any]]:
        return super().issues(**filters) if filters else list(self.rows.values())

    def write(self, number, title, body) -> int:
        post = {"body": body, "user": {"login": "github-actions[bot]"}}
        if number is None:
            self.rows[99] = {"number": 99, **post}
            return 99
        self.posts.setdefault(number, []).append(post)
        self.rows[number]["comments"] = len(self.posts[number])
        return number


@pytest.fixture
def git_graph(monkeypatch) -> None:
    promotion = "b" * 40
    baseline = "c" * 40
    squash = "d" * 40
    after_squash = "e" * 40
    graph = {
        SHA: [f"{SHA} {baseline}", baseline],
        promotion: [f"{promotion} {baseline} {SHA}", f"{SHA} {baseline}", baseline],
        baseline: [baseline],
        squash: [f"{squash} {baseline}", baseline],
        after_squash: [
            f"{after_squash} {squash}",
            f"{squash} {baseline}",
            baseline,
        ],
    }

    def git(*args: str) -> list[str]:
        return ["false"] if args[0] == "rev-parse" else graph[args[-1]]

    monkeypatch.setattr(cfr.dora_lead_time, "git", git)


@pytest.mark.parametrize("kind", ["rollback", "hotfix"])
def test_s037_create_incident(kind, git_graph) -> None:
    issues = Issues()
    hotfix = cfr.dora_lead_time.Pull(7, "main", SHA, START, feature=True, promotion=False)
    baseline = "c" * 40
    rows = (
        [
            arrival(1, CUTOFF - timedelta(hours=2), trigger="new_commit", commit={"id": baseline}),
            arrival(2, CUTOFF - timedelta(hours=1), trigger="new_commit", commit={"id": SHA}),
        ]
        if kind == "hotfix"
        else [
            arrival(1, CUTOFF - timedelta(hours=1), trigger="new_commit", commit={"id": baseline}),
            arrival(2, trigger="rollback", status="deactivated", commit={"id": baseline}),
        ]
    )
    corrections, gaps = cfr.find_corrections(REPO, SERVICE, rows, [hotfix], {7: ""}, {}, NOW)
    assert not gaps
    assert len(corrections) == 1
    cfr.record(issues, SERVICE, corrections[0])
    assert len(issues.rows) == 1
    body = issues.rows[99]["body"]
    expected = (
        f"https://dashboard.render.com/web/{SERVICE}/deploys/dep-2"
        if kind == "rollback"
        else f"https://github.com/{REPO}/pull/7"
    )
    assert expected in body
    assert "pending maintainer confirmation" in body


@pytest.mark.parametrize("mapped", [False, True], ids=["ancestry", "reviewed-mapping"])
def test_s038_linked_staging_hotfix(mapped, git_graph) -> None:
    issues = Issues(linked=True)
    revision = ("d" if mapped else "b") * 40
    hotfix = cfr.dora_lead_time.Pull(7, "staging", SHA, START, feature=True, promotion=False)
    promotion = cfr.dora_lead_time.Pull(8, "main", revision, START, feature=False, promotion=True)
    rows = [
        arrival(1, trigger="new_commit", commit={"id": revision}),
        arrival(2, CUTOFF + timedelta(minutes=1), trigger="new_commit", commit={"id": revision}),
    ]
    corrections, gaps = cfr.find_corrections(
        REPO,
        SERVICE,
        rows,
        [hotfix, promotion],
        {7: "Incident: #12"},
        {revision: [7]} if mapped else {},
        NOW,
    )
    assert not gaps
    assert len(corrections) == 1
    cfr.record(issues, SERVICE, corrections[0])
    assert set(issues.rows) == {12}
    body = issues.posts[12][0]["body"]
    assert f"https://github.com/{REPO}/pull/7" in body
    assert "pending maintainer confirmation" in body


def test_unmapped_squash_blocks_unverified_shipments(git_graph) -> None:
    revision = "d" * 40
    promotion = cfr.dora_lead_time.Pull(8, "main", revision, START, feature=False, promotion=True)
    corrections, gaps = cfr.find_corrections(
        REPO,
        SERVICE,
        [arrival(1, trigger="new_commit", commit={"id": revision})],
        [promotion],
        {},
        {},
        NOW,
    )
    assert not corrections
    assert gaps == [(CUTOFF, "dep-1: A deployed staging promotion requires reviewed provenance.")]


def test_s039_replay_preserves_attribution(monkeypatch) -> None:
    issues = Issues()
    corrective = cfr.Correction("dep-1", CUTOFF, "rollback", ("https://example.org/action",), None)
    write = issues.write

    def lost_response(number, title, body) -> int:
        write(number, title, body)
        raise cfr.EvidenceError("Response lost.")

    monkeypatch.setattr(issues, "write", lost_response)
    with pytest.raises(cfr.EvidenceError, match="Response lost"):
        cfr.record(issues, SERVICE, corrective)
    issues.rows[99]["body"] += "\nMaintainer attribution"
    cfr.record(issues, SERVICE, corrective)
    assert len(issues.rows) == 1
    assert issues.rows[99]["body"].count("https://example.org/action") == 1
    assert issues.rows[99]["body"].endswith("Maintainer attribution")


def test_s040_exclusive_start() -> None:
    result = report([arrival(i, START + timedelta(minutes=i)) for i in (-1, 0, 1)])
    assert START.isoformat() in result
    assert "Total production deployments: 1" in result
    assert "Change failure rate: 0%" in result


def test_s041_pending_cannot_change_count() -> None:
    result = report(
        [arrival(1, START + timedelta(minutes=1)), arrival(2, START + timedelta(hours=1))],
        [incident(None, CUTOFF, confirmed=False)],
    )
    assert "Requiring immediate intervention: 0" in result
    assert "Total production deployments: 2" in result
    assert "Change failure rate: 0%" in result


def test_scan_resumes_after_partial_run_and_report_names_pending_issue(
    monkeypatch, git_graph, tmp_path
) -> None:
    issues = Issues(linked=True)
    baseline = "c" * 40
    squash = "d" * 40
    hotfix = cfr.dora_lead_time.Pull(7, "staging", SHA, START, feature=True, promotion=False)
    promotion = cfr.dora_lead_time.Pull(8, "main", squash, START, feature=False, promotion=True)
    arrivals = [
        arrival(1, CUTOFF - timedelta(hours=4), trigger="new_commit", commit={"id": baseline}),
        arrival(2, CUTOFF - timedelta(hours=3), trigger="rollback", commit={"id": baseline}),
        arrival(3, CUTOFF, trigger="new_commit", commit={"id": squash}),
    ]
    monkeypatch.setattr(cfr, "configuration", lambda: (issues, SERVICE, "token", "dep-1"))
    monkeypatch.setattr(cfr.dora_evidence, "fetch_production_arrivals", lambda *_: arrivals)
    monkeypatch.setattr(
        cfr, "pull_evidence", lambda *_: ([hotfix, promotion], {7: "Incident: #12"})
    )
    manifest = tmp_path / "promotions.json"
    monkeypatch.setattr(cfr, "PROMOTIONS", manifest)

    assert cfr.main("reconcile", NOW) == 1
    assert set(issues.rows) == {12, 99}
    assert "dep-2" in issues.rows[99]["body"]
    assert not issues.posts

    manifest.write_text(f'{{"{squash}": [7]}}', encoding="utf-8")
    loaded = cfr.load_report(NOW)
    assert "dep-3: expected one GitHub incident entry." in report(*loaded)

    assert cfr.main("reconcile", NOW) == 0
    assert cfr.main("reconcile", NOW) == 0
    assert set(issues.rows) == {12, 99}
    assert len(issues.posts[12]) == 1

    summary = tmp_path / "summary"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert cfr.main("report", NOW) == 0
    rendered = summary.read_text()
    assert "Pending attribution on incident #12." in rendered
    assert "Pending attribution on incident #99." in rendered
    assert "Unavailable (incomplete evidence)" in rendered
    assert "expected one GitHub incident entry" not in rendered


def test_report_rejects_attribution_without_write_permission(monkeypatch) -> None:
    github = cfr.GitHub(REPO, "fixture-token")
    monkeypatch.setattr(github, "object_request", lambda path: {"permission": "read"})
    post = {
        "body": "DORA attribution: malformed",
        "user": {"login": "read-only", "type": "User"},
        "author_association": "MEMBER",
    }
    assert cfr.attributions(github, SERVICE, {12: [post]}) == ([], set(), [])


@pytest.mark.parametrize("evidence", ["missing-rollback", "wrong-hotfix-entry", "verified"])
@pytest.mark.parametrize("eligible_start", [True, False], ids=["in-time", "too-late"])
def test_s042_report_verifies_corrective_evidence(
    evidence, eligible_start, monkeypatch, git_graph
) -> None:
    issues = Issues()
    baseline = "c" * 40
    live = CUTOFF - timedelta(hours=2) if eligible_start else CUTOFF - timedelta(days=2)
    original = arrival(1, live, trigger="new_commit", commit={"id": baseline})
    kind = "rollback" if evidence == "missing-rollback" else "hotfix"
    pr_link = f"https://github.com/{REPO}/pull/7"
    link = (
        pr_link if kind == "hotfix" else f"https://dashboard.render.com/web/{SERVICE}/deploys/dep-2"
    )
    started = CUTOFF - timedelta(hours=1)
    encoded = json.dumps(
        {
            "service": SERVICE,
            "corrective": "dep-2",
            "original": "dep-1",
            "started": started.isoformat(),
            "status": "confirmed",
            "type": kind,
            "caused": True,
            "link": link,
        }
    )
    entry_link = f"https://github.com/{REPO}/pull/70" if evidence == "wrong-hotfix-entry" else link
    issues.rows[123] = {
        "number": 123,
        "user": {"login": "github-actions[bot]"},
        "body": f"{cfr.marker(SERVICE, 'dep-2')}\n- {entry_link}",
        "comments": 1,
    }
    issues.posts[123] = [{"body": f"DORA attribution: {encoded}"}]
    arrivals = [original]
    if kind == "hotfix":
        arrivals.append(arrival(2, NOW, trigger="new_commit", commit={"id": SHA}))
    pulls = [cfr.dora_lead_time.Pull(7, "main", SHA, START, feature=True, promotion=False)]
    monkeypatch.setattr(cfr, "configuration", lambda: (issues, SERVICE, "token", "dep-1"))
    monkeypatch.setattr(cfr.dora_evidence, "fetch_production_arrivals", lambda *_: arrivals)
    monkeypatch.setattr(cfr, "pull_evidence", lambda *_: (pulls, {7: ""}))

    result = report(*cfr.load_report(NOW))

    if not eligible_start:
        assert "Change failure rate: 0%" in result
    elif evidence == "verified":
        assert "Change failure rate: 100%" in result
    else:
        assert "Requiring immediate intervention (confirmed so far): 0" in result
        assert "Total production deployments (confirmed so far): 1" in result
        assert "Unavailable (incomplete evidence)" in result
        assert "#123" in result and "dep-2" in result


@pytest.mark.parametrize(
    ("kind", "revision"), [("rollback", "d"), ("hotfix", "a"), ("hotfix", "e")]
)
def test_s043_reconcile_independent_corrections(monkeypatch, git_graph, kind, revision) -> None:
    issues = Issues()
    squash = "d" * 40
    promotion = cfr.dora_lead_time.Pull(8, "main", squash, START, feature=False, promotion=True)
    pulls = [promotion]
    if kind == "hotfix":
        pulls.append(
            cfr.dora_lead_time.Pull(7, "main", revision * 40, START, feature=True, promotion=False)
        )
    arrivals = [
        arrival(1, CUTOFF - timedelta(hours=3), trigger="new_commit", commit={"id": squash}),
        arrival(
            2,
            CUTOFF,
            trigger="rollback" if kind == "rollback" else "new_commit",
            commit={"id": revision * 40},
        ),
    ]
    monkeypatch.setattr(cfr, "configuration", lambda: (issues, SERVICE, "token", "dep-1"))
    monkeypatch.setattr(cfr.dora_evidence, "fetch_production_arrivals", lambda *_: arrivals)
    monkeypatch.setattr(cfr, "pull_evidence", lambda *_: (pulls, {7: ""}))

    assert cfr.main("reconcile", NOW) == 1
    assert cfr.main("reconcile", NOW) == 1
    assert len(issues.rows) == 1
    body = issues.rows[99]["body"]
    assert body.count(cfr.marker(SERVICE, "dep-2")) == 1
    assert "pending maintainer confirmation" in body


@pytest.mark.parametrize("relevant", [True, False])
def test_s044_report_relevance_of_unresolved_provenance(monkeypatch, git_graph, relevant) -> None:
    issues = Issues()
    squash = "d" * 40
    baseline = "c" * 40
    promotion = cfr.dora_lead_time.Pull(8, "main", squash, START, feature=False, promotion=True)
    arrivals = [
        arrival(1, CUTOFF, trigger="new_commit", commit={"id": baseline}),
        arrival(2, NOW if relevant else START, trigger="new_commit", commit={"id": squash}),
    ]
    monkeypatch.setattr(cfr, "configuration", lambda: (issues, SERVICE, "token", "dep-2"))
    monkeypatch.setattr(cfr.dora_evidence, "fetch_production_arrivals", lambda *_: arrivals)
    monkeypatch.setattr(cfr, "pull_evidence", lambda *_: ([promotion], {}))

    result = report(*cfr.load_report(NOW))

    if relevant:
        assert "dep-2" in result and "reviewed provenance" in result
        assert "Unavailable (incomplete evidence)" in result
    else:
        assert "Change failure rate: 0%" in result
