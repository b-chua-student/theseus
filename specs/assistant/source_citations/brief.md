# Source citations in Assistant answers

Issue [#121](https://github.com/b-chua-student/theseus/issues/121)

## Goal

A Theseus user reading an Assistant answer can check a cited statement against the Source Library item that supports it.

## In Scope

- Associate cited statements with their supporting sources in the answer.
- Let the user open each cited source and use any available page number or passage location to find the evidence.
- Keep citations with the saved answer, so they appear when the conversation is reopened.
- Mark a citation as unavailable when its source has been removed.

## Non-Goals

The issue specifies no exclusions. The following are proposed and need confirmation:

- Extracting page numbers from file sources. Citations show a page only when one is already recorded.
- Jumping to or highlighting the evidence inside the opened source.

## Constraints

Every citation must refer to a Source Library item used as evidence for that answer. An answer that uses no source evidence shows no citations.

## Success Criteria

1. For each cited statement, the user can identify and open its supporting Source Library item from the answer.
2. If the evidence has a page number or passage location, the citation displays that location.
3. If the evidence has neither, the citation still identifies and opens the supporting item.

## Decisions Pending Confirmation

These were open questions. The scenarios assume the answers below.

- Opening a citation opens the source item only; it does not jump to the evidence (S-002, S-005).
- A saved answer keeps its citations (S-008). If the source was later removed, the citation keeps its title and location, is marked "no longer available", and cannot be opened (S-009).
