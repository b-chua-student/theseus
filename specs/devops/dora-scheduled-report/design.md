# Design — Scheduled DORA metrics report

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Add a dedicated GitHub Actions workflow with the UTC cron `0 16 * * 6` and `workflow_dispatch`. Both events invoke the same report job, which captures one UTC generation reference at the start of the run. Maintainers use manual dispatch to recover a dropped event. | `.github/workflows/dora-scheduled-report.yml`, consolidated report command | R-001, R-002, R-006, R-012 |
| D-002 | Reuse the five reporters' evidence readers, calculations, and supported reporting periods. Extract a callable report path where needed and have the standalone CLI call that same logic with its existing defaults and output behavior. Pass the run timestamp to metrics that use a time window and preserve each metric's window and boundary rules. | `scripts/dora_scheduled_report.py`, five standalone DORA reporters | R-005, R-008, R-009 |
| D-003 | Assemble the five sections independently. Keep the metric's existing evidence status and any valid partial results. Convert a known evidence failure that prevents rendering a section into a short, fixed explanation for that metric and continue with the remaining sections. Use safe diagnostics in published Markdown. | Consolidated report command, metric report functions | R-005, R-007, R-010 |
| D-004 | Render one UTF-8 Markdown file at `reports/dora/dora-report.md`. Publish its contents to the run summary and upload that exact file as a run artifact with its relative path preserved in the download. Use one summary step when the report fits and ordered summary steps when it exceeds the per-step limit. | Consolidated report command, GitHub Actions job summary and artifact upload | R-002, R-003, R-004, R-006, R-010 |
| D-005 | Run only the existing read-side reporting paths, including change failure rate report mode. Grant read access to repository contents, pull requests, and issues. Pass credentials only to the reporting step and stage the file in a run-local output directory. | Consolidated workflow, GitHub and Render evidence readers, change failure rate reporter | R-010, R-011 |

## Components and Flow

The scheduled and manual triggers start the same job. The job captures the UTC timestamp and calls the consolidated report command with the configuration used by the individual reporters. The command calls the five metric report functions, assembles their sections under a single report heading, and writes the Markdown once. The workflow uses that file for the job summary and artifact. If one metric encounters a known evidence gap, its section explains the gap and report generation continues.

## Data and Interfaces

- The job supplies the run timestamp, GitHub repository and read token, Render API key and production history configuration, and feature PR label through the workflow environment. Credentials are used only by evidence readers.
- Each metric supplies its Markdown result and any evidence gaps. Preserve existing behavior for verified empty results and partial evidence. Deployment frequency uses its existing verified production history, and time-windowed reports retain their respective periods.
- The artifact contains one UTF-8 Markdown file at `reports/dora/dora-report.md`. Upload from the output root with a path selection that preserves the `reports/dora/` directory in the download.

- Measure summary chunks in UTF-8 bytes against the 1 MiB per-step limit. Prefer complete Markdown blocks at chunk boundaries, preserve rendering for tables and other structured content, and verify that joining the source chunks reproduces the file byte for byte. GitHub displays up to 20 step summaries per job. If more chunks are needed, publish the additional chunks in ordered jobs on the same run page. [GitHub Actions job summary limits](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#step-isolation-and-limits)

## Evidence Outcomes

- The scheduled and manual jobs publish matching Markdown in the run summary and artifact, with one UTC generation timestamp and all five sections. Results agree with the individual reports for the same evidence and reference time.
- A report larger than 1 MiB is displayed in order across summary steps. The combined Markdown matches the single downloadable file.
- A dropped scheduled event is recovered only when a maintainer manually dispatches the workflow.
- When a metric lacks evidence, its section explains the gap while the four available results still appear.
- Both published copies exclude credentials. Existing individual reports still run through their original entry points. Reporting makes no deployment, incident, or repository writes.
