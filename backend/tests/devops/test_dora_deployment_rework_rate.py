from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from scripts import dora_deployment_rework_rate as rework
from scripts import dora_evidence

START = datetime(2026, 11, 26, 12, tzinfo=UTC)
SERVICE = "srv-prod"


def deploy(
    number, live=START - timedelta(days=1), status="live", **fields: object
) -> dict[str, Any]:
    return {
        "id": f"dep-{number}",
        "status": status,
        "createdAt": (live - timedelta(hours=1)).isoformat(),
        "finishedAt": live.isoformat(),
        **fields,
    }


def comment(*ids: int, login: str = "maintainer", service: str = SERVICE) -> dict[str, Any]:
    return {
        "body": "\n".join(f"/dora rework {service} dep-{number}" for number in ids),
        "user": {"login": login, "type": "User"},
    }


def incident(number, count, body="", title="[Production incident] Outage") -> dict[str, Any]:
    return {"number": number, "comments": count, "body": body, "title": title}


@pytest.fixture
def run_report(monkeypatch, tmp_path) -> Callable[..., str]:
    def run(
        deploys, issues=(), threads=None, anchor=None, *, partial=(), github_token="test"
    ) -> str:
        threads = threads or {}
        summary = tmp_path / "summary.md"
        settings = {
            "DORA_REPORT_STARTED_AT": START.isoformat(),
            "GITHUB_STEP_SUMMARY": str(summary),
            "GITHUB_REPOSITORY": "owner/repo",
            "GH_TOKEN": github_token,
            "RENDER_API_KEY": "test",
            "DORA_RENDER_SERVICE_ID": SERVICE,
            "DORA_RENDER_FIRST_DEPLOY_ID": anchor or (deploys[0]["id"] if deploys else "empty"),
        }
        for key, value in settings.items():
            monkeypatch.setenv(key, value)

        def request(url, token, source) -> tuple[list[dict[str, Any]], str]:
            if source == "Render":
                assert f"/services/{SERVICE}/deploys" in url
                if "cursor=" in url:
                    return [], ""
                return [{"deploy": row, "cursor": row["id"]} for row in deploys], ""
            if "/issues?" in url:
                assert deploys
                return list(issues), ""
            if "/comments?" in url:
                number = int(url.split("/issues/")[1].split("/")[0])
                if number not in threads or (number in partial and "&page=2" in url):
                    raise dora_evidence.EvidenceError("Comments unavailable.")
                link = 'rel="next"' if number in partial else ""
                return threads[number], link
            raise AssertionError(url)

        def permission(self, path) -> dict[str, str]:
            if path == "collaborators/unknown/permission":
                raise dora_evidence.EvidenceError("Permission unavailable.")
            role = "write" if path == "collaborators/maintainer/permission" else "read"
            return {"permission": role}

        monkeypatch.setattr(dora_evidence, "request", request)
        monkeypatch.setattr("scripts.dora_change_failure_rate.GitHub.object_request", permission)
        assert rework.main() == 0
        return summary.read_text()

    return run


def assert_rate(report, rework, total, rate) -> None:
    assert f"Rework deployments: {rework}\n" in report
    assert f"Production deployments: {total}\n" in report
    assert f"Deployment rework rate: {rate}\n" in report


def test_s064_unplanned_responses_to_infrastructure_outage(run_report) -> None:
    report = run_report(
        [
            deploy(1),
            deploy(2, status="deactivated"),
            deploy(3),
            deploy(4),
            deploy(5, status="build_failed"),
        ],
        [incident(1, 1, "Infrastructure outage"), incident(2, 1)],
        {1: [comment(1, 2)], 2: [comment(5)]},
    )
    assert_rate(report, 2, 4, "50%")


def test_s065_duplicate_confirmation(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2)],
        [incident(1, 1), incident(2, 1)],
        {1: [comment(1)], 2: [comment(1)]},
    )
    assert_rate(report, 1, 2, "50%")


def test_s066_live_time_and_manual_workflow(run_report) -> None:
    window_start = START - timedelta(days=30)
    report = run_report(
        [
            deploy(1, window_start - timedelta(seconds=1)),
            deploy(2, window_start),
            deploy(3, START - timedelta(seconds=1)),
            deploy(4, START),
            deploy(5, START + timedelta(seconds=1)),
        ],
        [incident(1, 1, "Outage began before the window.")],
        {1: [comment(1, 2, 4, 5)]},
    )
    assert_rate(report, 1, 2, "50%")
    assert window_start.isoformat() in report
    assert START.isoformat() in report

    path = Path(".github/workflows/dora-deployment-rework-rate.yml")
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read", "issues": "read"}
    steps = workflow["jobs"]["report"]["steps"]
    assert "date -u" in steps[0]["run"]
    assert "DORA_REPORT_STARTED_AT=" in steps[0]["run"]
    assert '>> "$GITHUB_ENV"' in steps[0]["run"]
    assert steps[-1]["run"] == "python scripts/dora_deployment_rework_rate.py"
    assert steps[-1]["env"] == {
        "GH_TOKEN": "${{ github.token }}",
        "RENDER_API_KEY": "${{ secrets.RENDER_API_KEY }}",
        "DORA_RENDER_SERVICE_ID": "${{ vars.DORA_RENDER_SERVICE_ID }}",
        "DORA_RENDER_FIRST_DEPLOY_ID": "${{ vars.DORA_RENDER_FIRST_DEPLOY_ID }}",
    }


@pytest.mark.parametrize("deploys", [[], [deploy(1, START)]])
def test_s067_verified_empty(run_report, deploys) -> None:
    assert_rate(run_report(deploys, [incident(1, 1)]), 0, 0, "N/A — no production deployments")


def test_s068_zero_without_valid_confirmation(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2)],
        [incident(1, 4, comment(2)["body"]), incident(2, 1, title="Unrelated issue")],
        {
            1: [
                comment(1, login="reader"),
                comment(1, service="srv-staging"),
                {"body": "/dora rework srv-prod dep-2 extra", "user": comment(2)["user"]},
                {"body": "```text\n/dora rework srv-prod dep-2\n```", "user": comment(2)["user"]},
            ],
            2: [comment(2)],
        },
    )
    assert_rate(report, 0, 2, "0%")


@pytest.mark.parametrize(
    "fields", [{"trigger": "rollback", "hotfix": True}, {}], ids=["S-069", "S-071"]
)
def test_unconfirmed_arrival_counts_only_in_total(run_report, fields) -> None:
    report = run_report([deploy(1), deploy(2, **fields)], [incident(1, 1)], {1: [comment(1)]})
    assert_rate(report, 1, 2, "50%")


def test_s070_incomplete_history(run_report) -> None:
    report = run_report([deploy(1)], anchor="dep-missing")
    assert "Incomplete evidence" in report
    assert "Production deployments: Unverified" in report
    assert "%" not in report


def test_s072_template() -> None:
    template = Path(".github/ISSUE_TEMPLATE/production-incident.md").read_text()
    section = template.split("## Deployment rework\n")[1]
    assert "went live in production as an unplanned response" in section
    assert "maintainer posts" in section
    assert "on its own line in an incident comment" in section
    assert "Record each qualifying deployment separately" in section
    assert "/dora rework <service-id> <deploy-id>" in section


def test_s074_unavailable_comments_preserve_confirmations(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2), deploy(3), deploy(4)],
        [incident(1, 1), incident(2, 1)],
        {2: [comment(1)]},
    )
    assert "Incomplete evidence" in report
    assert "Production deployments: 4\n" in report
    assert "Confirmed rework deployments: 1\n" in report
    assert "Deployments affected by the evidence gap: 3\n" in report
    assert "%" not in report


def test_s074_partial_thread_can_confirm_deployments_beyond_marker(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2)],
        [incident(1, 2, "<!-- dora-correction srv-prod/dep-1 -->")],
        {1: [comment(1)]},
        partial=(1,),
    )
    assert "Incomplete evidence" in report
    assert "Production deployments: 2\n" in report
    assert "Confirmed rework deployments: 1\n" in report
    assert "Deployments affected by the evidence gap: 1\n" in report
    assert "%" not in report


def test_incomplete_thread_keeps_rate_when_all_deployments_confirmed(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2)],
        [incident(1, 3, "<!-- dora-correction srv-prod/dep-1 -->")],
        {1: [comment(1), comment(2)]},
    )
    assert_rate(report, 2, 2, "100%")


def test_s073_permission_gap_is_scoped_to_the_command(run_report) -> None:
    report = run_report(
        [deploy(1), deploy(2), deploy(3)],
        [incident(1, 2)],
        {1: [comment(2, login="unknown"), comment(1)]},
    )
    assert "Confirmed rework deployments: 1\n" in report
    assert "Deployments affected by the evidence gap: 1\n" in report
    assert "%" not in report


def test_missing_github_access_preserves_the_verified_total(run_report) -> None:
    report = run_report([deploy(1)], github_token="")
    assert "Production deployments: 1\n" in report
    assert "Deployments affected by the evidence gap: 1\n" in report
    assert "%" not in report
