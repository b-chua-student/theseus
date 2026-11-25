import io
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from scripts import dora_evidence

WORKFLOW = Path(".github/workflows/dora-deployment-frequency.yml")
DAY = datetime(2026, 1, 1, tzinfo=UTC)


def deployment(
    number,
    hour,
    *,
    status="live",
    trigger="new_commit",
    day=DAY,
) -> dict[str, Any]:
    arrival = day + timedelta(hours=hour)
    return {
        "cursor": f"cursor-{number}",
        "deploy": {
            "id": f"dep-{number}",
            "createdAt": (arrival - timedelta(minutes=1)).isoformat(),
            "finishedAt": arrival.isoformat(),
            "status": status,
            "trigger": trigger,
            "commit": {"id": "a" * 40},
        },
    }


@pytest.fixture
def run_report(monkeypatch, tmp_path) -> Callable[..., str]:
    summary = tmp_path / "summary"
    monkeypatch.setenv("DORA_RENDER_SERVICE_ID", "srv-production")
    monkeypatch.setenv("RENDER_API_KEY", "fixture-token")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    def run(pages, *, first_id="dep-1", staging=(), expected_exit=0) -> str:
        from scripts import dora_deployment_frequency

        monkeypatch.setenv("DORA_RENDER_FIRST_DEPLOY_ID", first_id)
        by_cursor: dict[str | None, list[dict[str, Any]]] = {None: []}
        cursor = None
        for page in pages:
            by_cursor[cursor] = page
            cursor = page[-1]["cursor"]
            by_cursor[cursor] = []
        calls = []

        class FakeResponse(io.BytesIO):
            headers: dict[str, str] = {}

        class FakeOpener:
            def open(self, request, timeout) -> FakeResponse:
                parsed = urlsplit(request.full_url)
                assert (parsed.scheme, parsed.netloc) == ("https", "api.render.com")
                assert request.get_header("Authorization") == "Bearer fixture-token"
                assert request.get_method() == "GET"
                if parsed.path == "/v1/services/srv-staging/deploys":
                    rows = list(staging)
                else:
                    assert parsed.path == "/v1/services/srv-production/deploys"
                    query = parse_qs(parsed.query)
                    assert set(query) <= {"cursor", "limit"}
                    cursor = query.get("cursor", [None])[0]
                    calls.append(cursor)
                    rows = by_cursor[cursor]
                return FakeResponse(json.dumps(rows).encode())

        monkeypatch.setattr(dora_evidence, "build_opener", lambda *_: FakeOpener())
        assert dora_deployment_frequency.main() == expected_exit
        assert calls == list(by_cursor)
        if expected_exit:
            assert not summary.exists()
            return ""
        return summary.read_text()

    return run


def intervals(report) -> list[str]:
    return [line[2:] for line in report.splitlines() if line.startswith("- ")]


def test_s023_consecutive_intervals(run_report) -> None:
    assert intervals(run_report([[deployment(3, 14), deployment(1, 9), deployment(2, 11)]])) == [
        "2 hours",
        "3 hours",
    ]


def test_s024_excludes_staging_and_failed_attempts(run_report) -> None:
    production = [deployment(3, 13), deployment(2, 11, status="build_failed"), deployment(1, 9)]
    assert intervals(run_report([production], staging=[deployment(4, 10)])) == ["4 hours"]


def test_s021_includes_successful_manual_deployments(run_report) -> None:
    production = [
        deployment(3, 15, trigger="manual"),
        deployment(2, 11, trigger="manual", status="update_failed"),
        deployment(1, 9, status="deactivated"),
    ]
    assert intervals(run_report([production])) == ["6 hours"]


@pytest.mark.parametrize(
    ("pages", "first_id"),
    [([], "empty"), ([[deployment(2, 11), deployment(1, 9, status="build_failed")]], "dep-1")],
    ids=["never-deployed", "one-success-after-initial-failure"],
)
def test_s022_unavailable_with_fewer_than_two_successes(run_report, pages, first_id) -> None:
    report = run_report(pages, first_id=first_id)
    assert "Deployment interval unavailable" in report
    assert intervals(report) == []


@pytest.mark.parametrize(
    ("base", "action", "merged", "expected"),
    [
        ("main", "closed", True, True),
        ("main", "closed", False, False),
        ("staging", "closed", True, False),
        ("main", "opened", False, False),
    ],
)
def test_s025_only_merges_into_main_run_the_report(base, action, merged, expected) -> None:
    import yaml  # type: ignore[import-untyped]

    workflow = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    trigger = workflow["on"]["pull_request_target"]
    job = workflow["jobs"]["report"]
    assert job["if"] == "${{ github.event.pull_request.merged == true }}"
    assert (base in trigger["branches"] and action in trigger["types"] and merged) is expected
    assert job["steps"][-1]["run"] == "python -m scripts.dora_deployment_frequency"
    assert job["steps"][-1]["env"] == {
        "RENDER_API_KEY": "${{ secrets.RENDER_API_KEY }}",
        "DORA_RENDER_SERVICE_ID": "${{ vars.DORA_RENDER_SERVICE_ID }}",
        "DORA_RENDER_FIRST_DEPLOY_ID": "${{ vars.DORA_RENDER_FIRST_DEPLOY_ID }}",
    }


def test_s026_includes_oldest_page_without_time_cutoff(run_report) -> None:
    pages = [
        [deployment(3, 12), deployment(2, 9, status="deactivated")],
        [deployment(1, 9, day=datetime(2023, 1, 1, tzinfo=UTC), status="deactivated")],
    ]
    assert intervals(run_report(pages)) == ["1096 days", "3 hours"]


def test_s027_includes_successful_rollbacks_and_redeployments(run_report) -> None:
    production = [
        deployment(5, 13, trigger="manual"),
        deployment(4, 12, trigger="manual", status="build_failed"),
        deployment(3, 11, trigger="rollback", status="update_failed"),
        deployment(2, 10, trigger="rollback", status="deactivated"),
        deployment(1, 9, status="deactivated"),
    ]
    assert intervals(run_report([production])) == ["1 hour", "3 hours"]


@pytest.mark.parametrize(
    ("pages", "anchor"),
    [
        ([], "dep-1"),
        ([[deployment(1, 9)]], "empty"),
        ([[deployment(2, 11), deployment(1, 9)]], "dep-2"),
    ],
)
def test_rejects_history_with_unverified_anchor(run_report, capsys, pages, anchor) -> None:
    run_report(pages, first_id=anchor, expected_exit=1)
    assert "Render history does not match the verified first deployment." in capsys.readouterr().err
