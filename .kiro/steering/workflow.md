---
inclusion: always
---

Read `tasks.md` and `repo-findings.md` first when starting work; trust their contents. Do not issue directory listings unless a path is genuinely unknown. Read at most 2 reference files to confirm conventions — other specs are loaded on demand only. Do not inspect framework internals, type stubs, or installed library source.

Write code, then run `mypy backend/` and fix type errors immediately. Skip baseline test runs before making changes. After changes, run `ruff check backend/`, `mypy backend/`, and `pytest backend/` once each; fix what breaks. For broad or unfamiliar codebase exploration, delegate to the context-gatherer subagent rather than browsing file by file.

When dispatching subagents, pass at most 2-3 context files with the prompt. Trust subagent reports on lint, types, and tests — do not re-run those checks yourself or re-read files a subagent created just to verify them. Batch multiple independent tasks into a single subagent request instead of many small ones.

Skip task-tracking tools for small jobs. Skip `validate_spec_format` unless genuinely unsure of a spec's structure. Specs are the source of truth for a feature; reference them by path rather than pasting their contents into context.
