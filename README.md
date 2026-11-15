# Theseus

Theseus is a web-based document editor with Git-like version control and an AI research assistant.

- **Write** manuscripts made of nested sections, grouped into projects.
- **Version** your work with revisions (commits) and drafts (branches). Restore any earlier revision.
- **Cite** from a source library of papers and references.
- **Ask** an AI assistant (Gemini) questions about your manuscript.

## Documentation

| Document                                | Contents                                      |
| --------------------------------------- | --------------------------------------------- |
| [Setup guide](docs/setup.md)            | Install, configure, run, test, deploy         |
| [Architecture](docs/architecture.md)    | System diagram, bounded contexts, data flow   |
| [API reference](docs/api.md)            | Every HTTP endpoint, request and response     |

## Quick start

Requires Node.js 20+, Python 3.12+ and a MongoDB instance. Full details are in the [setup guide](docs/setup.md).

```bash
git clone https://github.com/b-chua-student/theseus
cd theseus
npm install                              # also installs frontend dependencies

python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env     # then set SECRET_KEY and GEMINI_API_KEY
npm run dev                              # frontend :5173, backend :5000
```

## Tech stack

| Layer    | Technology                                                            |
| -------- | --------------------------------------------------------------------- |
| Frontend | Svelte 5, Vite, Tiptap rich-text editor                            |
| Backend  | Python 3.12, Flask, Pydantic, Flask-Limiter, Gunicorn                 |
| Storage  | MongoDB (production), in-memory adapters (tests)                      |
| AI       | Google Gemini (chat), in-memory vector store (ChromaDB adapter exists, not wired) |
| Deploy   | Docker, Render                                                        |

## Project layout

```
backend/
  bootstrap/   app factory, dependency container, error handlers
  domain/      one package per bounded context (api, models, services, infrastructure)
  tests/
frontend/
  src/         Svelte pages, components, and API client (src/lib/api)
docs/          setup, architecture, API reference
```

## Branching Strategy

This project uses [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow).

- `main` is always deployable and protected. No direct pushes.
- All work happens on short-lived branches created from `main`.
- Branch names are descriptive and prefixed by type, e.g. `feat/user-collections`, `fix/env-validation`.

<img width="2358" height="748" alt="image" src="https://github.com/user-attachments/assets/dacc018c-93e5-4e07-acb7-7aa1c9f80b0d" />

### Workflow

1. Create a branch from `main`.
2. Commit changes using the Commitizen format (`feat(scope): message`).
3. Push the branch and open a pull request.
4. CI runs on the PR: install, lint, build. All checks must pass.
5. Request review and address feedback.
6. Merge into `main` after approval.
7. Delete the branch.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
