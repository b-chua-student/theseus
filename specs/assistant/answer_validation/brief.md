# Assistant answer validation — issue #125

## Goal
Give Theseus users answers that address their questions and accurately reflect evidence from the Source Library.

## In Scope
- Applies to assistant requests with the `source_library` context scope. Requests with the `none` or `manuscript` scope are not validated.
- Check relevance, claims, and citations during each source-backed request, before the answer is displayed or saved to the conversation.
- A citation is a reference from the answer to a retrieved Source Library passage. The user sees it as the passage's source location.
- Check relevance first. A draft that fails relevance is never displayed. It is replaced by a new draft while retries remain.
- Revise overstatements and mismatched citations, then validate the revision.
- If passages are insufficient, search again for better evidence and validate the resulting draft.
- A request with no usable Source Library passages and no retries left gets a limited answer that says the sources do not cover the question.

## Non-Goals
- Offline evaluation runs for maintainers are covered by a separate ticket (reference: TBD).
- Validation of `none` and `manuscript` scope answers.

## Constraints
- Validate before display and bound retries per request.
- Every retry type (claim revision, citation correction, new search, relevance redraft) counts against the same per-request retry limit.
- A withheld draft is not stored in the conversation history.
- If the model or a validator fails, the existing failure behavior applies: the pending exchange is discarded and the user can retry (`ChatModelError`, `ChatModelRateLimitedError`).
- Each validation adds model calls, so cost and latency per request grow with the retry limit.

## Open Product Decisions
These must be settled before implementation. The gherkin avoids fixing them.
- Retry limit per request (number).
- Acceptable wait time, and so whether validation runs synchronously inside the chat request.
- Whether the user sees intermediate status (for example "checking sources"), and through what mechanism.
- What the user sees when a draft fails relevance and no retries remain (fallback message or error).

## Success Criteria
- Display a relevant answer once its claims and citations pass validation.
- Withhold drafts that fail to address the question, and show the user a relevant answer or a fallback instead.
- Correct unsupported claims or mismatched citations and check the revision before display.
- Search again when evidence is insufficient and retries remain.
- At the retry limit, report what the sources support and identify remaining evidence gaps.
- Skip validation for requests that are not source-backed.
