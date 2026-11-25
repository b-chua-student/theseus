# Brief: Searchable PDFs

- ID: searchable-pdfs
- Owner: rhamy69
- Date: 2026-11-26
- Base SHA: bf695fe

## Goal

Allow researchers to search the text of uploaded PDFs through Source Library retrieval, including Assistant questions.

## Users / Roles

- Researchers.

## In Scope

- Make text from PDFs uploaded through issue #117 searchable.
- Retrieve matching passages and their pages when available.
- Support retrieval through Assistant questions.

## Non-Goals

- No additional exclusions specified.

## Constraints

- None specified.

## Known Touchpoints

- Source Library.
- Assistant.
- PDF Upload (#117).

## Assumptions

- No additional assumptions specified.

## Open Questions

- Should scanned PDFs require OCR? Deferred: Awaiting clarification.
- Should the library offer a dedicated full-text search? Deferred: Awaiting clarification.

## Success Criteria

1. A query about text in a searchable PDF can retrieve the matching passage and its page when available.

## Reference Links

- Ticket: `tickets/searchable-pdfs.md`
- GitHub issue: https://github.com/b-chua-student/theseus/issues/136
- Dependency: https://github.com/b-chua-student/theseus/issues/117
