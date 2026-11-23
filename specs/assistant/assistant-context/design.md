# Assistant context dropdown design

The composer tracks two values: whether to include the manuscript and the UUID of the selected source, if any. These values describe all four valid choices. None is derived when both are clear. Conversation identity is independent of these values.

## Composer and keyboard

In `frontend/src/components/chat/ChatPanel.svelte`, replace the scope buttons and nested source picker with one labelled menu button and a flat menu of checkable items. Derive checked states and the button label from the same two values. Use the source title for display and its UUID for selection and retrieval.

| Activated item | State update |
| --- | --- |
| Manuscript | Flip manuscript inclusion and retain the source. |
| Source title | Clear the UUID if already selected, otherwise replace it with this UUID. Retain manuscript inclusion. |
| None | Clear both values. This is idempotent. |

Use a menu button with expanded state and checked menu items that expose their state to assistive technology. On open, focus the first checked item. Arrow keys move through enabled items. Enter or Space applies the focused toggle and leaves the menu open. Escape or a second button activation closes it and returns focus to the button. Display both names for a combined selection, for example **Manuscript + Methods**.

`ChatPanel` receives an `editorReady` prop from `frontend/src/pages/editor.svelte`, true only when `loadState === 'ready'` and the editor exists. The `editor` object can exist before content has loaded, so it is not a readiness signal. The new-conversation default, the disabled Manuscript item and the restore timing all use `editorReady`.

## Source eligibility

Extend the existing source listing at `GET /api/sources?projectId=` with a boolean `indexed` on each entry. Wire the index-status lookup through a callable at bootstrap. The source-library domain consumes that callable without importing the assistant domain. The composer filters the current project's response for indexed entries. The chat service independently intersects requested IDs with eligible project documents at retrieval time, including if eligibility changed after the menu opened.

## Exchange contract

At send time, snapshot the selection and read the active editor text only if Manuscript is checked. Enforce the 500,000-character limit before creating or sending an exchange. Preserve the question when blocked.

| Selection | `context_scope` | `source_ids` | `manuscript_text` |
| --- | --- | --- | --- |
| None | `none` | null | Empty string |
| Manuscript | `manuscript` | null | Current editor text |
| One source | `source_library` | [selected UUID] | Empty string |
| Manuscript and one source | `manuscript_and_source` | [selected UUID] | Current editor text |

Extend the request model in `backend/domain/assistant/api/requests.py` and the service entry point in `backend/domain/assistant/services/chat.py`. Preserve existing request defaults and legacy source-only semantics for older callers.

Enforce the single UUID constraint for combined requests at both layers:

- `AskRequest` gets a model validator that rejects a missing, empty or multi-ID list, so the route returns its existing 400 for invalid requests.
- `ChatService.ask` repeats the check for direct callers. The route converts an empty list to `None` before calling the service, so the service treats `None` and an empty list the same way. It raises a new `AssistantError` subclass in `backend/domain/assistant/models/errors.py` with its own `code`. The existing `DomainError` handler in `backend/bootstrap/error_handlers.py` maps it to 400. A plain `ValueError` would fall through to the generic handler and return 500.
- Run this check before `conversation.ask(query)`. That call marks an exchange pending, and a rejection after it would block every later question in the conversation. Retrieval and the model call must not run for a rejected request.

In the chat service, decide independently whether to attach manuscript text and whether to retrieve passages. Combined scope enables both. Pass the labelled manuscript text, retrieved passages, question and existing conversation history to one model invocation. If the chosen source yields no passages, keep the retrieval result empty. Never broaden the search to another source.

## Thread lifecycle and persistence

Replace scope-keyed composer sessions with state tied to the active project and conversation. A context toggle updates only the next message's reference selection. A new chat initializes from editor readiness. Keep project changes and explicit conversation switches separate from context toggles.

On a successful exchange persist the scope and source IDs using the existing conversation fields. Return both on load. After the editor and project source list resolve, restore Manuscript for manuscript or combined scope and resolve exactly one eligible stored source for source-only or combined scope. Drop an unresolved or ambiguous source. Ignore stale load responses if the writer has switched projects or conversations.

Disable the dropdown during a send. On failure, keep the selected context, show the question and existing retry action, and re-enable the control. Try again resends the question with the selection and editor text current at that moment, because the control is enabled again after a failure and the writer may have changed it. Verify recovery in both source-only and combined modes.

Open decision: when a new conversation starts with the editor still loading, the selection is None. This design does not yet say whether it switches to Manuscript once the editor becomes ready or stays on None. Decide before implementing T6.

## Verification example

Set the unsaved draft to “We analysed 18 samples.” Give Methods a matching passage reporting 24 samples and Pilot one reporting 12. Select Manuscript + Methods and ask whether the sample counts agree. Inspect the request, retrieval filter and model input. The one call must contain the draft's 18 and Methods' 24, with no passage from Pilot. This checks evidence delivery without depending on exact model wording.
