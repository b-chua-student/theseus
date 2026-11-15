# Architecture

Theseus is a single deployable: a Svelte single-page app and a Flask API served from one origin. The
backend is organised as a set of **bounded contexts** using ports-and-adapters (hexagonal) design.

## System overview

```mermaid
flowchart LR
    Browser["Browser<br/>Svelte SPA"] -->|"HTTPS /api/* (session cookie)"| Flask

    subgraph Server["Flask app (Gunicorn, 1 worker)"]
        Flask["Blueprints<br/>(api layer)"] --> Services["Application services"]
        Services --> Domain["Domain models"]
        Services --> Ports["Ports"]
        Ports --> Adapters["Adapters"]
        Bus(("In-process<br/>event bus"))
    end

    Adapters --> Mongo[("MongoDB")]
    Adapters --> Vec[("Vector store<br/>in-memory")]
    Adapters --> Gemini["Google Gemini API"]
    Services <--> Bus
```

## Bounded contexts

```mermaid
flowchart TB
    Identity["identity<br/>accounts, login, sessions"]
    Project["project<br/>projects, members, ownership"]
    Manuscript["manuscript<br/>sections and text"]
    History["revision_history<br/>revisions + drafts"]
    SrcLib["src_lib<br/>source library"]
    Assistant["assistant<br/>indexing + chat (RAG)"]

    Project -. owner .-> Identity
    Manuscript -. belongs to .-> Project
    History -- "reads / writes via adapters" --> Manuscript
    Manuscript -- "ManuscriptSaved" --> Bus(("Event bus"))
    SrcLib -- "SourceAdded / SourceRemoved" --> Bus
    Bus --> Assistant
    Assistant -- "reads content" --> Manuscript
```

| Context            | Responsibility                                                              |
| ------------------ | --------------------------------------------------------------------------- |
| `identity`         | Register, log in, session identity. Passwords hashed with Argon2.           |
| `project`          | Create, rename, describe, delete projects; members; ownership transfer.    |
| `manuscript`       | Manuscripts with a tree of sections (heading, body, ordinal, parent).       |
| `revision_history` | Git-like history: revisions (commits) on drafts (branches); restore.        |
| `src_lib`          | Library of sources (title, authors, year, file reference).                  |
| `assistant`        | Index manuscripts into searchable chunks; answer questions with Gemini.     |

Contexts communicate through events on the in-process bus, not by calling each other's services.
`revision_history` reaches the manuscript through its own reader/writer adapters.

## Layering inside a context

```
domain/<context>/
  api/              Flask blueprint, Pydantic request models, API errors
  services/         Use cases (one class per operation)
  models/           Aggregates, entities, value objects, domain errors, events
  infrastructure/
    ports/          Interfaces the services depend on
    adapters/       In-memory and MongoDB (and Gemini/Chroma) implementations
```

Dependencies point inward: `api -> services -> models`, and services see only ports.
`bootstrap/` is the composition root. `build_container()` wires every module, defaulting to
in-memory adapters; `build_mongo_container()` swaps in MongoDB repositories. Tests use the
in-memory container, so they need no database or API key.

## Request flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant R as Route (blueprint)
    participant S as Service
    participant P as Port / Adapter
    B->>R: PUT /api/projects/{p}/manuscripts/{m}/sections/{s}/body
    R->>R: login_required, validate body (Pydantic)
    R->>S: edit_section_body.execute(...)
    S->>P: manuscript_repo.save(...)
    S-->>R: ok (publishes ManuscriptSaved)
    R-->>B: 204 No Content
```

Domain errors are mapped to JSON responses in one place, `bootstrap/error_handlers.py`.

## AI assistant (retrieval-augmented chat)

```mermaid
flowchart LR
    subgraph Ingest["Indexing (on ManuscriptSaved / SourceAdded)"]
        Evt["Event"] --> Q["Index job queue"] --> W["Ingestion worker"]
        W --> Parse["Parse"] --> Chunk["Chunk"] --> Embed["Embed"] --> Store[("Vector store")]
    end
    subgraph Ask["Chat"]
        Question["POST .../exchanges"] --> Search["Similarity search"]
        Store --> Search
        Search --> Gemini["Gemini chat model"] --> Answer["Answer"]
    end
```

Indexing runs asynchronously; poll `GET .../indexing-status` to see when a manuscript is searchable.

## Version control model

A manuscript has one or more **drafts** (branches). Each **revision** is an immutable snapshot of all
sections plus a message. `GET` on a manuscript returns the current draft's latest revision when history
exists; `?view=working` returns the working copy with uncommitted edits. Restoring a revision writes its
snapshot back into the working copy.

## Operational notes

- **Auth:** cookie session set by `/api/auth/login` and `/api/auth/register`.
- **Rate limits:** 100/day and 20/hour per IP by default; auth endpoints 5/minute. `/healthz` and static files are exempt.
- **Single worker:** the event bus, default vector store and limiter counters are in process memory.
- **Not yet wired:** the PostgreSQL identity adapter and the ChromaDB vector store exist but are unused. The vector store is in-memory, so the index is rebuilt after a restart.


### Draft merge semantics

A merge records one new revision on the current draft and replaces its working copy.
The source draft is unchanged. Merge provenance records the source name and head revision ID.
The merge base is the latest shared revision in target history, or the source head recorded
by a later target merge. Matching by revision ID preserves repeat-merge behavior after renames.

The pure merge engine compares heading, body, parent, and sibling rank independently. A
one-sided change wins; divergent edits require a target/source choice. Deletion versus an
unchanged section deletes it; deletion versus edits requires a whole-section choice, including
its descendants. Missing parents and parent cycles are conflicts. Output is deterministic
pre-order with consecutive sibling ordinals. Rank-based comparison can report ordering
conflicts when both drafts insert siblings.

The merge service rejects an uncommitted working copy and plans before writing. An in-process
lock prevents overlapping merges for a manuscript; optimistic history versions reject stale
repository saves. A failed history save removes the tentative revision and restores the old
working snapshot (rollback failures are logged). This is compensating rollback, not a database
transaction: process termination and concurrent manual edits are not covered by the lock.
Content replacement publishes `ManuscriptContentReplaced` for assistant re-indexing; identical
snapshots publish no event. Restore and draft switching use the same writer.
