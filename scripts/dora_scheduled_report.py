"""Generate and stage the consolidated, read-only DORA report."""

import argparse
import json
import os
import re
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

from scripts import (
    dora_change_failure_rate,
    dora_deployment_frequency,
    dora_deployment_rework_rate,
    dora_evidence,
    dora_failed_deployment_recovery_time,
    dora_lead_time,
)

REPORT = Path("reports/dora/dora-report.md")
SUMMARY_BYTES = 1024 * 1024
SUMMARIES_PER_JOB = 20
DETAILS = re.compile(rb"<details>.*?</details>\n?", re.DOTALL)
TABLE = re.compile(rb"(?m)^(?:\|[^\n]*\|\n)+")


def metric_section(title: str, report: Callable[[], str]) -> str:
    """Set the heading level and keep known evidence failures local to this metric."""
    try:
        _, _, body = report().partition("\n")
    except dora_evidence.EvidenceError as error:
        body = f"\nEvidence unavailable. {error}"
    except KeyError:
        body = "\nEvidence unavailable. Required configuration or evidence fields are missing."
    except (ValueError, TypeError, AttributeError, OverflowError):
        body = "\nEvidence unavailable. Source data could not be validated."
    body = re.sub(r"(?m)^Run time: [^\n]+\n\n", "", body)
    body = re.sub(r"(?m)^## ", "### ", body)
    return f"## {title}\n{body.rstrip()}\n"


def write_report(root: Path, now: datetime) -> None:
    """Write the single downloadable report from the existing metric readers."""
    now = now.astimezone(UTC)
    sections = (
        (dora_deployment_frequency.TITLE, dora_deployment_frequency.build_report),
        (dora_lead_time.TITLE, lambda: dora_lead_time.build_report(now)),
        ("DORA change failure rate", lambda: dora_change_failure_rate.build_report(now)),
        (
            "DORA failed deployment recovery time",
            lambda: dora_failed_deployment_recovery_time.report_from_environment(now),
        ),
        ("DORA deployment rework rate", lambda: dora_deployment_rework_rate.build_report(now)),
    )
    heading = f"# DORA metrics report\n\nGenerated at {now:%Y-%m-%d %H:%M:%S} UTC\n"
    report = "\n".join([heading, *(metric_section(title, read) for title, read in sections)])
    for name in ("GH_TOKEN", "RENDER_API_KEY"):
        if token := os.getenv(name):
            report = report.replace(token, "[redacted]")

    markdown = report.encode("utf-8")
    if len(markdown) > SUMMARY_BYTES:
        markdown = prepare_large_tables(markdown)
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(markdown)


def prepare_large_tables(markdown: bytes) -> bytes:
    """Repeat headers on oversized tables so each summary can render independently."""

    def expand_details(match: re.Match[bytes]) -> bytes:
        block = match[0]
        if len(block) <= SUMMARY_BYTES:
            return block
        # The lead time reporter wraps its evidence table in a collapsible block.
        label = re.search(rb"<summary>(.*?)</summary>", block)
        heading = b"### " + label[1] + b"\n\n" if label else b""
        table = TABLE.search(block)
        return heading + table[0] if table else block

    def split_table(match: re.Match[bytes]) -> bytes:
        table = match[0]
        if len(table) <= SUMMARY_BYTES:
            return table
        header, separator, *rows = table.splitlines(keepends=True)
        prefix = header + separator
        groups = []
        group = bytearray(prefix)
        for row in rows:
            if len(group) > len(prefix) and len(group) + len(row) + 1 > SUMMARY_BYTES:
                groups.append(bytes(group))
                group = bytearray(prefix)
            group.extend(row)
        groups.append(bytes(group))
        return b"\n".join(groups)

    return TABLE.sub(split_table, DETAILS.sub(expand_details, markdown))


def markdown_blocks(markdown: bytes) -> Iterator[bytes]:
    """Keep collapsible evidence and paragraph blocks together where possible."""
    cursor = 0
    for details in DETAILS.finditer(markdown):
        yield from re.findall(rb".+?(?:\n\n|\Z)", markdown[cursor : details.start()], re.DOTALL)
        yield details[0]
        cursor = details.end()
    yield from re.findall(rb".+?(?:\n\n|\Z)", markdown[cursor:], re.DOTALL)


def summary_chunks(markdown: bytes) -> Iterator[bytes]:
    """Split the exact UTF-8 report at Markdown blocks, then lines if needed."""
    if len(markdown) <= SUMMARY_BYTES:
        if markdown:
            yield markdown
        return
    chunk = bytearray()
    for block in markdown_blocks(markdown):
        if chunk and len(chunk) + len(block) > SUMMARY_BYTES:
            yield bytes(chunk)
            chunk.clear()
        start = 0
        while len(block) - start > SUMMARY_BYTES:
            limit = start + SUMMARY_BYTES
            end = block.rfind(b"\n", start, limit) + 1
            if end <= start:
                end = limit
                while block[end] & 0b11000000 == 0b10000000:
                    end -= 1
            yield block[start:end]
            start = end
        chunk.extend(block[start:])
    if chunk:
        yield bytes(chunk)


def stage_summaries(root: Path, group: int | None = None) -> list[int]:
    """Stage ordered summary slots and return the overflow job groups."""
    summaries = root / "summary"
    summaries.mkdir(exist_ok=True)
    chunks = summary_chunks((root / REPORT).read_bytes())
    selected_group = 1 if group is None else group
    last_group = 0
    for index, chunk in enumerate(chunks):
        group_index, slot = divmod(index, SUMMARIES_PER_JOB)
        last_group = group_index + 1
        if last_group == selected_group:
            (summaries / f"{last_group}-{slot + 1}.md").write_bytes(chunk)
    return list(range(2, last_group + 1))


def main() -> None:
    """Generate the artifact or prepare summary files from the shared artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("report", "stage"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--group", type=int)
    args = parser.parse_args()
    if args.command == "report":
        now = dora_evidence.timestamp(os.environ["DORA_REPORT_STARTED_AT"])
        write_report(args.root, now)
        return
    overflow = stage_summaries(args.root, args.group)
    if args.group is None:
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"overflow={json.dumps(overflow)}\n")


if __name__ == "__main__":
    main()
