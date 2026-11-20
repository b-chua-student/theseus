# Feature intake — Assistant Context

## Goal

As a writer, I want to choose what the Assistant can consult for my next question while staying in the manuscript editor.

## Starting State

- The Assistant sidebar is `frontend/src/components/chat/ChatPanel.svelte`, shown by `frontend/src/pages/editor.svelte`.
- The panel has three toggle buttons (None, Manuscript, Source Library) marked with `aria-pressed`, a context summary line, and a "Select sources" picker with an "All library sources" checkbox.
- The panel starts in `none` and resets to `none` when the project changes. The backend default for a new conversation is `source_library`.
- The panel keeps a separate session (message list and conversation) for each scope and source selection. It says "Changing sources starts a separate conversation." Switching scope therefore shows a different thread and does not carry history across modes.
- Ticking every source in the picker stores an explicit list of IDs, not "all".
- The picker lists sources from `listSources(projectId)` (`/api/sources?projectId=`). `GET /api/sources?projectId=` returns every active source of the project (`id`, `kind`, `title`, `authors`, `year`, `file_ref`) with no indexing status, so the picker cannot tell indexed sources from others. The backend retrieval already drops sources that are not indexed.
- The client already sends `POST /api/projects/:projectId/conversations/:conversationId/exchanges` with `{query, context_scope, source_ids, manuscript_text}`. It sends `source_ids: null` and `manuscript_text: ""` when they are unused. The editor text is read at send time.
- The backend contract in `backend/domain/assistant/api` accepts that body and needs no change. The routes are registered in `backend/bootstrap/app.py` at `/api/projects/<project_id>/conversations` and `/api/sources`. Opening a saved conversation already restores its stored `context_scope` and `source_ids`.
- A failed send leaves the question in the thread with an error reply and a Try again action. A 404 for a missing conversation silently starts a new conversation.

## In Scope

- Replace the three scope buttons with one compact **Context** button. Its collapsed label shows the current choice.
- Offer exactly three radio items in one menu: **Manuscript**, **Sources**, and **None**. Sources refers to the current project's Source Library. There is no combined Manuscript and Source Library choice.
- Make **Sources** the default for a new conversation (a change from the current `none`).
- In Sources mode, let the writer use all eligible project sources or narrow retrieval to specific library entries. The source picker sits inside Sources mode.
- Use one conversation per chat. Switching mode or source selection does not start another conversation and does not hide earlier exchanges.
- Block sending an over-long manuscript before any request is made.

## Non-Goals

Changes to manuscript editing, source uploads, indexing, retrieval ranking, saved-conversation listing, or the backend exchange contract are outside this feature.

## Definitions

- **Eligible source:** a source in the current project whose indexed document has status `INDEXED` (searchable). Sources from other projects, and sources not yet indexed or failed, are not eligible.
- **All sources:** the default picker state. The request sends `source_ids: null`.
- **Narrowed selection:** at least one eligible entry is unchecked. The request sends the checked IDs. If the writer checks every entry again, the picker returns to All sources and the request sends `source_ids: null`.
- **Cleared selection:** every entry is unchecked. The request sends `source_ids: []`.
- **Sends no X:** the client sends `null` for `source_ids` or `""` for `manuscript_text`. The backend ignores both outside the scope that uses them.

## Constraints

- Choose one mode per message and read the active mode, selection, and editor text when the writer sends.
- “None” controls new reference material for a turn. The conversation history stays available in every mode.
- The source selection is kept when the writer switches to another mode and back within the same conversation.
- The editor sends `manuscript_text` of at most 500,000 characters and at most 1,000 `source_ids`. If the manuscript is longer in Manuscript mode, the composer tells the writer and does not send. The typed question stays in the composer.
- If a send fails, the writer's chosen mode and source selection stay as they were. The question stays in the thread, and the error reply offers Try again.
- If the conversation no longer exists (404), the writer is told and the question is kept. The app does not silently start a new conversation.
- When an existing conversation is opened, the Context button shows its stored `context_scope` and `source_ids`. A new conversation starts at Sources with All sources.
- The Sources picker lists only eligible sources. If the project has none, Sources stays selectable, the picker says there are no searchable sources, and the Assistant answers without library material. The source list response has no indexing status, so showing only eligible entries needs the list to carry one. Adding it is a backend change and is the one exception to "no backend change". If it is not added, the picker lists all project sources and retrieval ignores the ones that are not indexed.
- Manuscript is unavailable until the editor is ready. Context controls are disabled while a message is in flight.

| Menu item | `context_scope` | Reference input for this message |
| --- | --- | --- |
| Manuscript | `manuscript` | Send the current editor text as `manuscript_text`, including unsaved edits. Send no source IDs and skip library retrieval. |
| Sources | `source_library` | Send no manuscript text. Send `source_ids` as `null` for all eligible sources, the chosen IDs for a narrowed selection, or `[]` for a cleared selection. |
| None | `none` | Send no manuscript text and no source IDs. Skip library retrieval. |

## Success Criteria

1. The composer has one Context button. In a new conversation it shows Sources. Opening it exposes exactly the three named radio items with only Sources checked.
2. Selecting an item checks only that item, updates the button label, and closes the menu. A keyboard user can open it (focus starts on the checked item), move between choices, confirm a choice, or dismiss it with Escape.
3. In Manuscript mode, the Assistant receives the text visible in the editor at send time and retrieves no sources.
4. In Sources mode, retrieval uses only eligible sources from the current project within the chosen selection. A cleared selection retrieves nothing. The request sends no manuscript text.
5. In None mode, the next message has no new manuscript or library material. Prior exchanges remain available in the conversation, as they are in every mode.
6. Switching modes before sending applies only the final choice to that message, however many times the writer switched. The thread and its earlier exchanges stay visible and unchanged.
7. A failed send keeps the chosen mode and source selection. Reopening an existing conversation restores its stored mode and selection.
