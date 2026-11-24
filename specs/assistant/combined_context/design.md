# Design — Compare a manuscript with selected library sources

## Design

| ID | Decision | Components | Requirements |
| --- | --- | --- | --- |
| D-001 | Capture editor.getText() and the checked library entry IDs at send time. Capture an exact quote separately from the question. Carry the snapshot in one exchange on the active conversation. | ChatPanel.svelte, chat.js, AskRequest, exchange route | R-001, R-003, R-004 |
| D-002 | Normalize the request into independent manuscript and library inputs. Keep legacy scope decoding at the API boundary. Intersect requested IDs with active sources in the authorized project before any vector query. Use live draft text directly. | requests.py, routes.py, ChatService, project source lookup | R-001, R-004 |
| D-003 | Embed the question with the quoted claim when present and query eligible passages by source. Attach the library entry ID and title to each supplied passage. Use the same semantic embedding model for indexing and queries, and rebuild incompatible hash-based vectors before enabling semantic search. | ChatService, embedding generator, indexing service, VectorStore, container.py | R-002, R-003, R-004 |
| D-004 | Pass labelled draft, quote, question and source excerpts through the chat model port. Identify the quote as the comparison target. Map citation identifiers to supplied excerpts and render their source titles. | ChatModel, GeminiChatModel, FakeChatModel, ChatPanel.svelte | R-001, R-002, R-003, R-004 |

### Conditional design for the existing scenarios

These proposals depend on the ticket decisions listed under Open Questions.

- Use one checkbox dropdown with a scrollable, title-filtered source list and fixed controls. Derive the all-selected indicator from indexed IDs across the entire project list. Bulk selection copies that set once. Keep selection independent of filter, quote and conversation identity. Expose project-scoped indexing status alongside library titles.
- Encode Web and Manuscript independently with explicit selected UUIDs. Web alone retains legacy scope none. Accept selections above 1,000 without truncation and batch downstream work. On success, save the flags and selected ID/title pairs together. Restore from both conversation repositories, decoding legacy manuscript, none and library scopes. Resolve a legacy all-library selection against the project when converting it to an explicit set.
- Isolate failed searches by source. Apply a calibrated cosine threshold inclusively. Allocate eligible passages in rounds across sources, trying smaller fitting passages before marking a source omitted. Compute the evidence budget from the configured model window minus tokens for instructions, history, question, selected draft, quote, formatting and reserved response. Count the assembled request before dispatch.
- Pass named outcomes and only admitted excerpts to the model. Distinguish support, qualification and conflicting facts. Mark missing evidence as unverifiable. Web enables separately identified model knowledge. It adds no browsing.
