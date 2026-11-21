# Feature intake — Assistant chat context dropdown

## Goal

A writer can ask “Does this source support the claim in my manuscript?” and have the Assistant consult both the current draft and the chosen source for the same answer.

## In Scope

Replace the separate context buttons and source picker with one **Context** dropdown. It lists **Manuscript** first, then each searchable source in the current project's Source Library by title, then **None**. The writer can include the manuscript, one source, or both.

- Toggle Manuscript independently. Choosing a different source replaces the previous source and preserves the Manuscript setting.
- Choosing None clears both selections. Removing the last selected item also selects None. Choosing any material clears None.
- Each toggle takes effect immediately. The menu stays open so the writer can make both selections in one visit. The button summarizes the selection, for example **Manuscript + Methods**.

## Non-Goals

Source uploads, indexing jobs, retrieval ranking, selecting multiple library sources for one message, and changes to chat history are outside this feature.

## Constraints

A searchable source is an indexed entry in the current project. The source list response (`GET /api/sources?projectId=`) exposes an `indexed` flag. The source library reads it through a callable that bootstrap injects, so it does not import the assistant context. Each menu item identifies its source by UUID.

Extend the exchange and saved conversation contracts to recognize `manuscript_and_source`. Keep the three existing scopes valid. This changes the accepted scope values in the request model, the chat service, and the stored conversation. For this scope the chat service retrieves from the chosen source and adds the manuscript text to the same model call. The composer sends the following values according to the selection at send time.

| Selection | `context_scope` | `manuscript_text` | `source_ids` |
| --- | --- | --- | --- |
| None | `none` | Empty string | `null` |
| Manuscript | `manuscript` | Current editor text | `null` |
| One source | `source_library` | Empty string | List containing the selected UUID |
| Manuscript + one source | `manuscript_and_source` | Current editor text | List containing the selected UUID |

- Combined requests require exactly one source UUID. Reject a missing, empty, or multi-ID selection before retrieval or model invocation.
- Read manuscript text at send time, including unsaved edits. If Manuscript is selected and the text exceeds 500,000 characters, keep the typed question and tell the writer why sending is blocked.
- A new conversation starts on Manuscript when the editor is ready and on None otherwise. Manuscript is unavailable while the editor is loading.
- Restore a saved selection once the editor and source list are ready. If the stored source is no longer eligible, drop that source and keep Manuscript if it was selected. A legacy source-only selection with zero, multiple, or null source IDs opens on None. A saved `manuscript_and_source` selection with null, empty, or multiple source IDs opens on Manuscript.
- Opening the menu focuses the first checked item in display order. Arrow keys move focus, Space or Enter toggles the focused item, and Escape closes the menu and returns focus to the button. Activating the button also closes the menu. Moving focus alone preserves the selection.
- Activating None while it is checked changes nothing.
- Changing context keeps earlier exchanges in the same conversation. Disable the control during a send and keep the selection if the send fails.

## Success Criteria

1. One dropdown lists Manuscript, searchable project sources by title, and None. An empty source list leaves Manuscript and None available when the editor is ready.
2. A writer can toggle Manuscript and a source in either order, replace or deselect a source, or clear both. The button and checked items reflect the same selection after mouse or keyboard interaction.
3. Manuscript alone supplies the latest editor text and skips library retrieval. The manuscript size limit applies whenever Manuscript is selected, including alongside a source.
4. A source selection restricts retrieval to that source. Choosing another source limits the next answer to passages from the newly selected source, alongside manuscript text if selected.
5. None clears both inputs for the next message. The Assistant receives no new manuscript text and performs no library retrieval for that message.
6. New and reopened conversations display their initial or saved choices. Changing context preserves the thread, and the control is disabled while a send is in flight.
7. After a failed send, the selected context stays visible and the question remains in the thread with a **Try again** action.
8. With Manuscript and one source selected, the same model call receives the latest manuscript text and matching passages retrieved only from that source, so one answer can compare the two.
