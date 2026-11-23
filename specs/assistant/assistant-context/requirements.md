# Assistant context dropdown requirements

A writer asking “Does this study support my manuscript claim?” must be able to supply the current draft and one chosen study to the Assistant in the same exchange.

The requirement numbers correspond to the eight success criteria in the feature intake. Scenario IDs refer to `assistant-context-dropdown.feature`.

| ID | Acceptance requirement | Scenarios |
| --- | --- | --- |
| R1 | Provide one Context dropdown. List Manuscript first, each indexed source in the current project by title in library order, then None. Identify sources by UUID. An empty list leaves Manuscript and None. | S-033, S-034, S-051 |
| R2 | Toggle Manuscript independently of one source. Selecting another source replaces the first. Selecting None clears both. Removing the last item selects None. Activating None again keeps it selected. Apply changes immediately and keep the menu open. Show the selection on the button. | S-035, S-036, S-037, S-048, S-054, S-057, S-058 |
| R3 | Read manuscript text, including unsaved edits, at send time. Manuscript alone skips retrieval. Accept exactly 500,000 characters. Above that limit, explain the issue, retain the typed question and block the request only when Manuscript is selected. | S-038, S-043, S-047, S-061, S-062 |
| R4 | A source-only message sends its explicit UUID and empty manuscript text. Retrieve matching passages only from that eligible source, even if other sources match or the selected source is the only one listed. | S-039, S-040, S-041 |
| R5 | With None selected, send empty manuscript text and null source IDs. Skip library retrieval for the turn. | S-042, S-043 |
| R6 | Default a new conversation to Manuscript if the editor is ready, otherwise None. Disable Manuscript while loading and the whole control during a send. Keep earlier exchanges in the same thread across selection changes. Persist and restore the saved selection, including combined context. Accept existing exchange scopes. | S-044, S-045, S-049, S-050, S-055, S-059, S-060 |
| R7 | After a failed send, preserve the context selection and show the question in the thread with a Try again action. Try again uses the selection current when it is activated. | S-046 |
| R8 | A combined exchange supplies current manuscript text and matching passages from exactly one selected source to the same model call. Reject missing, null, empty or multiple source IDs for combined requests before retrieval or model invocation. | S-052, S-053, S-056 |

## Keyboard interaction

Opening the menu focuses the first checked item in display order. Arrow keys move focus without changing the selection. Enter or Space activates an item. Escape closes the menu and returns focus to the button. Activating the button also closes the menu. Reopening shows the committed choices.

## Restoring a conversation

After the editor and project source list are ready, restore a source only if exactly one stored UUID identifies an eligible entry. Otherwise restore None for source-only history or Manuscript for combined history. This applies to removed or unindexed sources and legacy null, empty or multiple-ID selections.

## Scope

The feature supports one library source per message. The dropdown does not offer an all-sources choice, although the backend keeps its existing handling of `source_library` requests that send null source IDs. Changing uploads or indexing jobs, tuning retrieval ranking and changing conversation history content are outside scope.
