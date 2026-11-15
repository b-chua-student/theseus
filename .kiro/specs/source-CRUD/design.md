# Design: Source Library Text Upload

Req IDs → `requirements.md`. Layer paths relative to `backend/domain/src_lib/`.

## Decisions

| # | Decision | Why |
|---|----------|-----|
| D1 | **Extend `Source`** with `kind: "file"\|"text"` (default `file`) + optional text fields. | Reuses repo, soft delete, events, assistant pipeline. `kind` is separate from `contentType`. |
| D2 | **New `/text` sub-resource**; existing endpoints untouched. | Matches intake/feature; zero change to file-source contract (N4). |
| D3 | **Embed content** in the Source Mongo doc. | ≤100K chars ≪ 16 MB doc cap; no join. WiredTiger compresses; no app-level compression. |
| D4 | **Version = int counter**, bumped on each update; no history. Last-write-wins. | Matches "basic version tracking". |
| D5 | **Search: Mongo `$text`** (project-scoped); in-memory adapter uses token/substring match. | No new infra. ChromaDB stays assistant-only. |
| D6 | `file_ref` becomes optional; invariant in aggregate. | Text sources have no file. |
| D7 | Sanitize by **not rendering as HTML** (no `{@html}`), typed queries, no string-built filters. Stored verbatim. | Preserves N5; safest XSS model. |
| D8 | Body cap 512 KB (100K chars × ≤4 B UTF-8 + metadata); route-level limit via Flask `MAX_CONTENT_LENGTH` check or per-route guard. | R9. |
| D9 | `isActive` ≡ `removed_at is None` (no new field). | Existing soft delete. |
| D10 | `userId` ≡ existing project scoping; follow current routes' project resolution. | Existing auth model. |

## Domain

```python
# value_objects.py (new)
Description(str ≤1000) · Tags(tuple[str,...] ≤10, normalized) · ContentType(Enum) · TextBody(str 1..100_000)

# aggregates.py
class Source:  # existing fields +
    kind: Literal["file","text"] = "file"
    file_ref: str | None            # required iff kind=="file"
    content: TextBody | None        # required iff kind=="text"
    description: Description | None
    tags: Tags = Tags(())
    content_type: ContentType = OTHER
    version: int = 1
    updated_at: datetime | None
    def update_text(...) -> SourceUpdated   # validates, version+=1
```
Invariants enforced in constructor/factory: `kind=text ⇒ content∧¬file_ref`; `kind=file ⇒ file_ref∧¬content`. `authors`/`year` stay empty/None for text.

Events (`events.py`): `SourceAdded` gains `kind` (default `file` for old consumers); new `SourceUpdated(source_id, project_id, kind, version)`; `SourceRemoved` unchanged.

## Services (`services/`)
`AddTextSource`, `UpdateTextSource`, `GetSource` (reuse), `ListTextSources(filters, sort, page)`, `SearchTextSources(q, filters, page)`, `RemoveSource` (reuse). Wired in container as `container.source.<op>`.

## Ports/Adapters (`infrastructure/`)
`SourceRepository` adds: `list_text(project_id, content_type?, tag?, sort, page, page_size)`, `search_text(project_id, q, filters, page, page_size)`; `save` handles update.
- **Mongo**: list uses projection excluding `content` (+ compute `snippet` via `$substrCP` or in adapter). Indexes: `(project_id, kind, removed_at, updated_at)`, `(project_id, tags)`, text index on `title(10) tags(5) description(3) content(1)`. Mongo allows one text index per collection → **extend existing if present**. Missing new fields on old docs read as defaults (N4).
- **In-memory**: same semantics for tests.

## API (`api/`) — all `@login_required`, project-scoped like existing routes

| Method | Path | Notes |
|--------|------|-------|
| POST | `/text` | 201 → DTO. Limiter on. |
| GET | `/text` | `?contentType&tag&sort=updatedAt\|title&page&pageSize` |
| GET | `/text/search` | `?q&contentType&tag&page&pageSize` (register before `/text/<id>`) |
| GET | `/text/<id>` | DTO with content |
| PUT | `/text/<id>` | Full replace of editable fields. Limiter on. |
| DELETE | `/text/<id>` | 204; delegates to `RemoveSource` |

Request models (`requests.py`): `TextSourceRequest` (shared by POST/PUT; Pydantic limits per R1; strip tags). Errors → 400 `{errors:[{field,message}]}`, 404 via `SourceNotFoundError`, 429 via Flask-Limiter.

DTO: `{id, kind, title, description, tags, contentType, content?, snippet?, version, createdAt, updatedAt}` (`content` only on detail; `snippet` only on list/search). List/search envelope: `{items,total,page,pageSize}`.

Existing `GET /` includes text sources as summaries (`kind` field added; additive only).

## Assistant integration
- `on_source_added`: if `kind=text`, ingest `content` directly (skip file fetch).
- New `on_source_updated`: re-ingest (delete old chunks, add new).
- `on_source_removed`: unchanged (verify it keys by source id).
- `source_content_provider`: return `content` when `kind=text`.
- *Verify first:* `ingestion_worker.py` assumptions about `file_ref`.

## Frontend (`frontend/src/`)
- `lib/api/textSources.ts` — typed client for table above.
- `components/text-sources/`: `TextSourceForm.svelte` (metadata left, content right, counter, preview toggle as `<pre>`), `TextSourceList.svelte` + `TextSourceCard.svelte` (search/filter/sort, pagination), `ConfirmDelete`.
- Draft autosave: debounced (1 s) `localStorage["theseus:text-draft:<projectId>"]`; cleared on successful save; restored on mount.
- Never use `{@html}` for user content. Labels, focus order, `aria-live` errors, responsive layout.

## Test strategy
Unit (domain, services) with in-memory adapter → API tests (Flask client) bound to feature scenarios → Mongo integration + perf (N1–N3) → frontend component tests → UI scenarios (`@ui`).

## Risks
Single Mongo text index conflict · `file_ref` assumptions in ingestion · route ordering (`/text/search`) · large-payload limiter tuning.
