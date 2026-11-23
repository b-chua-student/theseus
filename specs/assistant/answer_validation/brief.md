# Assistant answer validation — issue #125

## Goal
Give Theseus users answers that address their questions and accurately reflect evidence from the Source Library.

## In Scope
Check relevance, claims, and citations during each source-backed request. Revise overstatements. If passages are insufficient, search for better evidence and validate the resulting draft.

## Non-Goals
Offline evaluation runs for maintainers are covered by a separate ticket.

## Constraints
Validate before display and bound retries per request. The retry count, acceptable wait time, and intermediate status behavior remain open product decisions.

## Success Criteria
- Display a relevant answer once its claims and citations pass validation.
- Withhold drafts that fail to address the question.
- Correct unsupported claims or mismatched citations and check the revision before display.
- Search again when evidence is insufficient and retries remain.
- At the retry limit, report what the sources support and identify remaining evidence gaps.
