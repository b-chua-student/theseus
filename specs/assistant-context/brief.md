# Feature intake — Assistant Context

## Goal

As a writer, I want to choose what the Assistant can consult for my next question while staying in the manuscript editor.

## Starting State

- The editor's Assistant sidebar (`frontend/src/components/editor.svelte`) has no context controls and no source picker. It posts `{document_id, message, document}` to the legacy `/api/chat` endpoint and never starts a conversation.
- The backend already implements the target contract in `backend/domain/assistant/api`: `POST .../conversations/{conversation_id}/exchanges` with `{query, context_scope, manuscript_text, source_ids}`. It requires a signed-in project member and an existing conversation. This feature needs no backend contract change.
- The work is therefore: start or open a conversation from the editor, send through the real exchange endpoint, and add the Context control and source picker.

## In Scope

- Add one compact **Context** button to the Assistant composer. Its collapsed label shows the current choice.
- Offer exactly three radio items in one menu: **Manuscript**, **Sources**, and **None**. Sources refers to the current project's Source Library. There is no combined Manuscript and Source Library choice.
- In Sources mode, let the writer use all eligible project sources or narrow retrieval to specific library entries. The source picker sits inside Sources mode.
- Send each message through the exchange endpoint using the chosen scope.

## Non-Goals

Changes to manuscript editing, source uploads, indexing, retrieval ranking, chat history management, or the backend exchange contract are outside this feature.

## Definitions

- **Eligible source:** a source in the current project whose indexed document has status `INDEXED` (searchable). Sources from other projects, and sources not yet indexed or failed, are not eligible.
- **All sources:** the untouched default state of the picker. The request omits `source_ids`.
- **Narrowed selection:** the writer has unchecked at least one eligible entry. The request sends the checked IDs. If the writer re-checks every entry, the picker returns to All sources and the request omits `source_ids`.
- **Cleared selection:** the writer has unchecked every entry. The request sends `[]`.

## Constraints

- Keep the existing new-conversation default of **Sources**. Choose one mode per message and read the active selection when the writer sends it.
- “None” controls new reference material for a turn. The conversation history stays available in every mode.
- The source selection is kept when the writer switches to another mode and back within the same conversation.
- The editor sends `manuscript_text` of at most 500,000 characters and at most 1,000 `source_ids`. If the manuscript is longer in Manuscript mode, the composer tells the writer and does not send. The typed question is kept.
- If a send fails, the writer's chosen mode, source selection, and typed question stay as they were so the writer can retry.
- When an existing conversation is opened, the Context button shows that conversation's stored `context_scope` and `source_ids`. A new conversation starts at Sources with All sources.
- The Sources picker lists only eligible sources. If the project has none, Sources stays selectable, the picker says there are no searchable sources, and the Assistant answers without library material.

| Menu item | `context_scope` | Reference input for this message |
| --- | --- | --- |
| Manuscript | `manuscript` | Send the current editor text as `manuscript_text`, including unsaved edits. Omit `source_ids` and skip library retrieval. |
| Sources | `source_library` | Omit `manuscript_text`. Omit `source_ids` for all eligible sources, send chosen IDs for a narrowed selection, or send `[]` for a cleared selection. |
| None | `none` | Omit `manuscript_text` and `source_ids`. Skip library retrieval. |

## Success Criteria

1. The composer has one Context button. In a new conversation it shows Sources. Opening it exposes exactly the three named radio items with only Sources checked.
2. Selecting an item checks only that item, updates the button label, and closes the menu. A keyboard user can open it (focus starts on the checked item), move between choices, confirm a choice, or dismiss it with Escape.
3. In Manuscript mode, the Assistant receives the text visible in the editor at send time and retrieves no sources.
4. In Sources mode, retrieval uses only eligible sources from the current project within the chosen selection. A cleared selection retrieves nothing. The request omits manuscript text.
5. In None mode, the next message has no new manuscript or library material. Prior exchanges remain available in the conversation, as they are in every mode.
6. Switching modes before sending applies only the final choice to that message, however many times the writer switched. Earlier exchanges keep their original content.
7. A failed send keeps the chosen mode, source selection, and typed question. Reopening an existing conversation restores its stored mode and selection.
