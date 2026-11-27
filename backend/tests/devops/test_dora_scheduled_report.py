import io
import json
import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Self
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import pytest
import yaml  # type: ignore[import-untyped]
from scripts import (
    dora_change_failure_rate,
    dora_deployment_frequency,
    dora_deployment_rework_rate,
    dora_evidence,
    dora_failed_deployment_recovery_time,
    dora_lead_time,
)

WORKFLOW = Path(".github/workflows/dora-scheduled-report.yml")
REPORT = Path("reports/dora/dora-report.md")
SATURDAY = datetime(2026, 11, 28, 16, tzinfo=UTC)
TOKENS = {"GH_TOKEN": "github-fixture-secret", "RENDER_API_KEY": "render-fixture-secret"}
METRICS = (
    "Successful production deployments: 2",
    "Median lead time (hours): 1.00",
    "Change failure rate: 0%",
    "Completed recoveries: 0",
    "Deployment rework rate: 0%",
)


@pytest.fixture
def evidence(monkeypatch) -> Iterator[None]:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    settings = {
        **TOKENS,
        "GITHUB_REPOSITORY": "example/theseus",
        "DORA_RENDER_SERVICE_ID": "srv-production",
        "DORA_RENDER_FIRST_DEPLOY_ID": "dep-1",
        "DORA_FEATURE_LABEL": "feature",
    }
    for key, value in settings.items():
        monkeypatch.setenv(key, value)

    live = SATURDAY - timedelta(days=3)
    deploys: list[dict[str, object]] = [
        {
            "cursor": str(index),
            "deploy": {
                "id": f"dep-{index}",
                "createdAt": (arrival - timedelta(minutes=1)).isoformat(),
                "finishedAt": arrival.isoformat(),
                "status": "live",
                "trigger": "new_commit",
                "commit": {"id": revision},
            },
        }
        for index, arrival in enumerate((live, live + timedelta(hours=2)), 1)
    ]
    pulls: list[dict[str, object]] = [
        {
            "number": 10,
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
            "labels": [{"name": "feature"}],
            "merge_commit_sha": revision,
            "merged_at": (live - timedelta(hours=1)).isoformat(),
        }
    ]
    requests = []

    class Response(io.BytesIO):
        headers: dict[str, str] = {}

    class Opener:
        def open(self, request, timeout) -> Response:
            url = urlsplit(request.full_url)
            requests.append(request.get_method())
            assert request.get_method() == "GET"
            if url.netloc == "api.render.com":
                assert request.get_header("Authorization") == f"Bearer {TOKENS['RENDER_API_KEY']}"
                assert url.path == "/v1/services/srv-production/deploys"
                rows = [] if "cursor=" in url.query else deploys
            else:
                assert url.netloc == "api.github.com"
                assert request.get_header("Authorization") == f"Bearer {TOKENS['GH_TOKEN']}"
                if url.path == "/repos/example/theseus/labels/dora-recovery-incident":
                    return Response(b'{"name":"dora-recovery-incident"}')
                assert url.path in {"/repos/example/theseus/pulls", "/repos/example/theseus/issues"}
                rows = pulls if url.path.endswith("/pulls") else []
            return Response(json.dumps(rows).encode())

    monkeypatch.setattr(dora_evidence, "build_opener", lambda *_: Opener())
    monkeypatch.setattr(dora_change_failure_rate, "build_opener", lambda *_: Opener())

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None) -> Self:
            if tz is None:
                return cls.fromisoformat(SATURDAY.replace(tzinfo=None).isoformat())
            return cls.fromtimestamp(SATURDAY.timestamp(), tz)

    monkeypatch.setattr(dora_lead_time, "datetime", Clock)
    yield
    assert requests and set(requests) == {"GET"}


def workflow() -> dict:
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def publish(tmp_path, monkeypatch, now) -> str:
    from scripts import dora_scheduled_report as scheduled

    monkeypatch.setenv("DORA_REPORT_STARTED_AT", now.isoformat())
    scheduled.write_report(tmp_path, now)
    assert [path.relative_to(tmp_path) for path in tmp_path.rglob("*.md")] == [REPORT]
    artifact = (tmp_path / REPORT).read_bytes()
    assert b"".join(scheduled.summary_chunks(artifact)) == artifact
    report = artifact.decode()
    for token in TOKENS.values():
        assert token not in report
    assert report.count("## DORA ") == 4
    assert "## Feature PR merge-to-production lead time" in report
    assert f"{now:%Y-%m-%d %H:%M:%S} UTC" in report
    return report


def test_s079_scheduled_report(tmp_path, monkeypatch, evidence) -> None:
    config = workflow()
    assert config["on"]["schedule"] == [{"cron": "0 16 * * 6"}]
    assert SATURDAY.astimezone(ZoneInfo("Asia/Manila")).strftime("%A %H:%M") == "Sunday 00:00"
    assert config["permissions"] == dict.fromkeys(("contents", "pull-requests", "issues"), "read")
    steps = config["jobs"]["report"]["steps"]
    assert (
        sum("python -m scripts.dora_scheduled_report report" in s.get("run", "") for s in steps)
        == 1
    )
    uploads = [s for s in steps if s.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(uploads) == 1
    assert uploads[0]["with"]["path"].endswith("/**/dora-report.md")
    status = subprocess.check_output(["git", "status", "--porcelain"])
    report = publish(tmp_path, monkeypatch, SATURDAY)
    assert subprocess.check_output(["git", "status", "--porcelain"]) == status
    assert all(metric in report for metric in METRICS)

    standalone = tmp_path / "standalone"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(standalone))
    for reporter in (
        dora_deployment_frequency.main,
        lambda: dora_change_failure_rate.main("report", SATURDAY),
        dora_failed_deployment_recovery_time.main,
        dora_deployment_rework_rate.main,
    ):
        assert reporter() == 0
    assert all(metric in standalone.read_text() for metric in METRICS if "lead time" not in metric)
    assert dora_lead_time.main() == 0
    assert METRICS[1] in standalone.read_text()


def test_s081_manual_report(tmp_path, monkeypatch, evidence) -> None:
    assert "workflow_dispatch" in workflow()["on"]
    assert all(
        metric in publish(tmp_path, monkeypatch, SATURDAY + timedelta(hours=1))
        for metric in METRICS
    )


def test_s080_missing_evidence(tmp_path, monkeypatch, evidence) -> None:
    def unavailable(*args: object) -> list:
        raise dora_evidence.EvidenceError(f"GitHub evidence request failed. {TOKENS['GH_TOKEN']}")

    monkeypatch.setattr(dora_lead_time, "fetch_pulls", unavailable)
    report = publish(tmp_path, monkeypatch, SATURDAY)
    assert "GitHub evidence request failed." in report
    assert METRICS[1] not in report
    assert all(metric in report for metric in (*METRICS[:1], *METRICS[2:]))


def test_s082_manual_recovery() -> None:
    config = workflow()
    assert set(config["on"]) == {"schedule", "workflow_dispatch"}
    assert "if" not in config["jobs"]["report"]
    assert "workflow_dispatch" not in str(config["jobs"])


def test_s083_full_ordered_summary(tmp_path) -> None:
    from scripts import dora_scheduled_report as scheduled

    limit = 1024 * 1024
    assert list(scheduled.summary_chunks(b"a" * limit)) == [b"a" * limit]
    line = ("é" * 4096 + "\n").encode()
    report = line * 2600
    chunks = list(scheduled.summary_chunks(report))
    assert len(chunks) > 20
    assert all(0 < len(chunk) <= limit and chunk.decode() for chunk in chunks)
    assert b"".join(chunks) == report

    config = workflow()["jobs"]
    published = []
    for group, job_name in ((1, "report"), (2, "summary")):
        runner = tmp_path / job_name
        root = runner / "dora-report"
        (root / REPORT).parent.mkdir(parents=True)
        (root / REPORT).write_bytes(report)
        assert scheduled.stage_summaries(root, None if group == 1 else group) == [2]
        steps = [
            step["run"]
            for step in config[job_name]["steps"]
            if step.get("run", "").startswith("bash scripts/publish_dora_summary.sh ")
        ]
        assert len(steps) == 20
        for command in steps:
            summary = runner / "step-summary"
            summary.unlink(missing_ok=True)
            subprocess.run(
                ["bash", "-e", "-c", command],
                check=True,
                env={
                    "DORA_SUMMARY_GROUP": str(group),
                    "RUNNER_TEMP": str(runner),
                    "GITHUB_STEP_SUMMARY": str(summary),
                },
            )
            if summary.exists():
                published.append(summary.read_bytes())
    assert published == chunks
    assert config["summary"]["needs"] == "report"
    assert config["summary"]["strategy"]["max-parallel"] == "1"

    table = b"| Incident | Status |\n| --- | --- |\n" + b"| #1 | Unresolved |\n" * 60000
    markdown = scheduled.prepare_large_tables(
        b"<details><summary>Evidence</summary>\n\n" + table + b"\n</details>\n"
    )
    table_chunks = list(scheduled.summary_chunks(markdown))
    assert b"".join(table_chunks) == markdown
    assert all(
        b"| Incident | Status |\n| --- | --- |\n" in chunk
        for chunk in table_chunks
        if b"| #1 |" in chunk
    )
    assert markdown.count(b"| #1 |") == 60000
