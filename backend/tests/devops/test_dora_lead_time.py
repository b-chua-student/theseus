from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Never
from urllib.parse import parse_qs, urlsplit

import pytest
from scripts import dora_lead_time as dora

END = datetime(2026, 11, 24, tzinfo=UTC)
START = END - timedelta(days=30)
LIVE = START + timedelta(days=1)


def sha(number) -> str:
    return f"{number:040x}"


def pull(number, hours, *, base="staging", promotion=False) -> dora.Pull:
    return dora.Pull(
        number, base, sha(number), LIVE - timedelta(hours=hours), not promotion, promotion
    )


def deploy(number, revision, live=LIVE) -> dora.Deploy:
    return dora.Deploy(f"dep-{number}", revision, live)


@pytest.fixture
def graph(monkeypatch) -> None:
    parents = {
        sha(1): [],
        sha(2): [sha(1)],
        sha(3): [sha(11)],
        sha(11): [sha(2)],
        sha(4): [sha(1)],
        sha(5): [sha(4), sha(3)],
        sha(6): [sha(4)],
        sha(7): [sha(5)],
        sha(8): [sha(1)],
        sha(9): [sha(8)],
        sha(10): [sha(9)],
    }

    def ancestors(revision) -> set[str]:
        if revision not in parents:
            raise dora.EvidenceError("Required Git revision history is unavailable.")
        return {revision}.union(*(ancestors(parent) for parent in parents[revision]))

    def git(*args: str) -> list[str]:
        if args[0] == "rev-parse":
            return ["false"]
        assert args[:2] == ("rev-list", "--parents")
        return [" ".join((sha, *parents[sha])) for sha in ancestors(args[-1])]

    monkeypatch.setattr(dora, "git", git)


def report(
    pulls, deployments, manifest=None
) -> tuple[datetime, list[tuple[dora.Pull, dora.Deploy]], float | None]:
    traces = dora.resolve(pulls, deployments, manifest or {}, END)
    return dora.calculate(traces, END)


def test_multi_pr_promotion_preserves_original_merges(graph) -> None:
    pulls = [pull(1, 10), pull(2, 6), pull(3, 2), pull(5, 1, base="main", promotion=True)]
    start, included, hours = report(pulls, [deploy(1, sha(5))])
    assert start == START
    assert [pr.number for pr, _ in included] == [1, 2, 3]
    assert hours == 6
    summary = dora.format_report(start, END, included, hours)
    assert dora.TITLE in summary
    assert START.isoformat() in summary and END.isoformat() in summary
    assert "Included feature PR count: 3" in summary


def test_squash_promotion_uses_reviewed_evidence(graph) -> None:
    feature, promotion = pull(3, 8), pull(6, 2, base="main", promotion=True)
    assert report([feature, promotion], [deploy(1, sha(6))], {sha(6): [3]})[2] == 8
    with pytest.raises(dora.EvidenceError, match="requires reviewed provenance"):
        report([feature, promotion], [deploy(1, sha(6))])
    with pytest.raises(dora.EvidenceError, match="references an invalid PR"):
        report([feature, promotion], [deploy(1, sha(6))], {sha(6): [123]})


def test_direct_feature_and_redeploy(graph) -> None:
    feature = pull(4, 3, base="main")
    first = deploy(1, sha(4))
    later = deploy(2, sha(7), LIVE + timedelta(hours=21))
    assert report([feature], [later, first]) == (START, [(feature, first)], 3)


def test_window_boundaries_even_median_and_empty_report(graph) -> None:
    old = deploy(1, sha(1), START - timedelta(seconds=1))
    lower = deploy(2, sha(4), START)
    upper = deploy(3, sha(7), END)
    pulls = [pull(1, 48), pull(4, 48, base="main"), pull(7, 6, base="main")]
    assert report(pulls, [old, lower, upper]) == (START, [(pulls[1], lower)], 24)
    assert report(pulls, [old, upper]) == (START, [], None)
    assert "Median lead time (hours): Unavailable" in dora.format_report(START, END, [], None)
    start, included, hours = report(pulls, [deploy(4, sha(7))])
    assert start == START and len(included) == 3 and hours == 48
    _, included, hours = report(pulls[:2], [deploy(5, sha(4))])
    assert len(included) == 2 and hours == 48
    _, included, hours = report([pull(1, 72), pull(4, 6, base="main")], [deploy(6, sha(4))])
    assert len(included) == 2 and hours == 39


def render_row(number, status, *, commit=4, created=LIVE, finished=LIVE) -> dict[str, Any]:
    return {
        "cursor": f"cursor-{number}",
        "deploy": {
            "id": f"dep-{number}",
            "createdAt": created.isoformat(),
            "finishedAt": finished.isoformat(),
            "status": status,
            "commit": {"id": sha(commit)},
        },
    }


def test_render_paginates_production_and_excludes_unsuccessful_deploys(monkeypatch, graph) -> None:
    calls = []

    def request(url, token, source) -> tuple[list[dict[str, Any]], str]:
        assert urlsplit(url).path == "/v1/services/srv-production/deploys"
        assert token == "fixture-render-token" and source == "Render"
        cursor = parse_qs(urlsplit(url).query).get("cursor", [None])[0]
        calls.append(cursor)
        pages = {
            None: [
                render_row(3, "live", finished=LIVE + timedelta(hours=4)),
                render_row(2, "build_failed", commit=3),
            ],
            "cursor-2": [render_row(1, "deactivated", created=LIVE - timedelta(hours=1))],
            "cursor-1": [],
        }
        return pages[cursor], ""

    monkeypatch.setattr(dora, "request", request)
    deployments = dora.fetch_deploys("srv-production", "fixture-render-token", "dep-1")
    feature = pull(4, 6, base="main")
    assert report([feature, pull(3, 6)], deployments) == (START, [(feature, deploy(1, sha(4)))], 6)
    assert calls == [None, "cursor-2", "cursor-1"]
    with pytest.raises(dora.EvidenceError, match="verified first deployment"):
        dora.fetch_deploys("srv-production", "fixture-render-token", "dep-9")


def test_github_pagination_and_feature_classification(monkeypatch) -> None:
    def request(url, token, source) -> tuple[list[dict[str, Any]], str]:
        assert urlsplit(url).path == "/repos/owner/repo/pulls"
        assert token == "fixture-github-token" and source == "GitHub"
        number = int(parse_qs(urlsplit(url).query)["page"][0])
        row = {
            "number": number,
            "merged_at": (LIVE - timedelta(hours=6)).isoformat(),
            "base": {"ref": "main"},
            "merge_commit_sha": sha(number),
            "head": {
                "ref": "staging" if number == 2 else "change",
                "repo": {"full_name": "owner/repo"},
            },
            "labels": [{"name": "Feature"}],
        }
        return [row], '<https://api.github.com/next>; rel="next"' if number == 1 else ""

    monkeypatch.setattr(dora, "request", request)
    assert dora.fetch_pulls("owner/repo", "fixture-github-token", "feature", END) == [
        pull(1, 6, base="main"),
        pull(2, 6, base="main", promotion=True),
    ]


@pytest.fixture
def workflow_env(monkeypatch, tmp_path) -> Path:
    summary = tmp_path / "summary"
    for key, value in {
        "GITHUB_REPOSITORY": "owner/repo",
        "GH_TOKEN": "fixture-github-token",
        "DORA_RENDER_SERVICE_ID": "srv-production",
        "RENDER_API_KEY": "fixture-render-token",
        "DORA_RENDER_FIRST_DEPLOY_ID": "dep-1",
        "DORA_FEATURE_LABEL": "feature",
        "GITHUB_STEP_SUMMARY": str(summary),
    }.items():
        monkeypatch.setenv(key, value)
    return summary


def test_credential_bearing_error_publishes_no_metrics(monkeypatch, capsys, workflow_env) -> None:
    class BrokenOpener:
        def open(self, request, timeout) -> Never:
            raise OSError(f"private response mentioning {request.headers['Authorization']}")

    monkeypatch.setattr(dora, "build_opener", lambda *_: BrokenOpener())
    assert dora.main() == 1
    assert capsys.readouterr() == ("", "Render evidence request failed.\n")
    assert not workflow_env.exists()


def test_missing_promotion_publishes_no_metrics(monkeypatch, capsys, workflow_env, graph) -> None:
    monkeypatch.setattr(dora, "fetch_deploys", lambda *args: [deploy(1, sha(6))])
    monkeypatch.setattr(
        dora, "fetch_pulls", lambda *args: [pull(6, 2, base="main", promotion=True)]
    )
    monkeypatch.setattr(dora, "promotion_manifest", dict)
    assert dora.main() == 1
    assert capsys.readouterr() == (
        "",
        "A deployed staging promotion requires reviewed provenance.\n",
    )
    assert not workflow_env.exists()


def test_manual_entrypoint_writes_verified_fixture_summary(
    monkeypatch, workflow_env, graph
) -> None:
    class Clock:
        @classmethod
        def now(cls, tz=None) -> datetime:
            return END

    monkeypatch.setattr(dora, "datetime", Clock)
    monkeypatch.setattr(dora, "fetch_deploys", lambda *args: [deploy(1, sha(4))])
    monkeypatch.setattr(dora, "fetch_pulls", lambda *args: [pull(4, 3, base="main")])
    monkeypatch.setattr(dora, "promotion_manifest", dict)
    assert dora.main() == 0
    summary = workflow_env.read_text()
    assert "Median lead time (hours): 3.00" in summary
    assert "Included feature PR count: 1" in summary
    assert "fixture-" not in summary


@pytest.mark.parametrize(("first_id", "valid"), [("empty", True), ("dep-1", False)])
def test_empty_render_history_requires_verified_empty_anchor(monkeypatch, first_id, valid) -> None:
    monkeypatch.setattr(dora, "request", lambda *args: ([], ""))
    if valid:
        assert dora.fetch_deploys("srv-production", "fixture-render-token", first_id) == []
    else:
        with pytest.raises(dora.EvidenceError, match="verified first deployment"):
            dora.fetch_deploys("srv-production", "fixture-render-token", first_id)


def test_weekly_job_defaults_to_withheld() -> None:
    import yaml  # type: ignore[import-untyped]

    workflow = yaml.load(
        Path(".github/workflows/dora-lead-time.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert workflow["on"] == {
        "workflow_dispatch": "",
        "schedule": [{"cron": "23 9 * * 1"}],
    }
    assert workflow["jobs"]["report"]["if"] == (
        "github.event_name == 'workflow_dispatch' || vars.DORA_WEEKLY_ENABLED == 'true'"
    )
