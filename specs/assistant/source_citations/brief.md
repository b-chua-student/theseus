# Source citations in Assistant answers

Issue [#121](https://github.com/b-chua-student/theseus/issues/121)

## Goal

A Theseus user reading an Assistant answer can check a cited statement against the Source Library item that supports it.

## In Scope

- Associate cited statements with their supporting sources in the answer.
- Let the user open each cited source and use any available page number or passage location to find the evidence.

## Non-Goals

The issue specifies no exclusions.

## Constraints

Every citation must refer to a Source Library item used as evidence for that answer.

## Success Criteria

1. For each cited statement, the user can identify and open its supporting Source Library item from the answer.
2. If the evidence has a page number or passage location, the citation displays that location.
3. If the evidence has neither, the citation still identifies and opens the supporting item.

## Open Questions

- Should opening a citation jump directly to the evidence when the source supports it?
- What should a saved answer show or do if its cited source later becomes unavailable or is removed?
