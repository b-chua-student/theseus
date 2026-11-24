---
inclusion: always
---

Follow the ticket-to-implementation workflow in [AGENTS.md](../../AGENTS.md), including the approval gate after intake and Gherkin. Use the repository templates when authoring feature specs.

For implementation, open `tasks.md` in the relevant feature directory. Follow the task's dependencies and verification instructions, and use its `R-###`, `D-###`, and `S-###` references to find the matching requirements, design decisions, and scenarios. Consult `repo-findings.md` for repository conventions as needed.

Write code, then run `mypy backend/` and fix type errors immediately. Skip baseline test runs before making changes. After changes, run `ruff check backend/`, `mypy backend/`, and `pytest backend/` once each; fix what breaks. For broad or unfamiliar codebase exploration, delegate to the context-gatherer subagent rather than browsing file by file.

When dispatching subagents, pass at most 2-3 context files with the prompt. Trust subagent reports on lint, types, and tests — do not re-run those checks yourself or re-read files a subagent created just to verify them. Batch multiple independent tasks into a single subagent request instead of many small ones.

Skip task-tracking tools for small jobs. When authoring or updating feature specs, check ticket line references, cross-file coverage, and task dependencies against the templates. Reference spec files by path in agent context.
