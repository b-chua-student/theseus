# Theseus _(theseus)_

A web-based manuscript editor with draft branches, revision history, and a source-aware writing assistant.

Theseus gives writers a workspace to revise manuscripts, preserve earlier drafts, and ask questions about their manuscript and source material.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Verification](#verification)
- [Team Roles](#team-roles)
- [Tech Stack and Architecture](#tech-stack-and-architecture)
- [Production and Release](#production-and-release)
- [DevOps and Delivery](#devops-and-delivery)
- [API](#api)
- [Contributing](#contributing)
- [License](#license)

## Install

### Dependencies

Install Git. For native development, install Node.js 24 with npm and Python 3.12. For container-based setup, install Docker. A MongoDB instance is needed for data to persist across restarts.

### Local Setup

```sh
git clone https://github.com/b-chua-student/theseus.git
cd theseus
npm ci
python3.12 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
```

On Windows, use `py -3.12 -m venv backend/.venv` and activate it in PowerShell with `.\backend\.venv\Scripts\Activate.ps1`.

The default local setup uses in-memory data. For MongoDB persistence or live Gemini calls, copy the [environment template](backend/.env.example) to `backend/.env` and set the values for your environment. Keep credentials in your local environment or the hosting secret store. See the [local reviewer setup](docs/local-setup.md).

#### Build with Docker

Clone the repository and build from its root so Docker can access both the frontend and backend. The [Dockerfile](Dockerfile) builds the Svelte app and packages it with Flask and Gunicorn. The build downloads the MiniLM model.

```sh
docker build -t theseus:local .
```

## Usage

Run this from the repository root with the Python environment active.

```sh
npm run dev
```

Open the URL printed by Vite. Vite forwards API requests to Flask on port 5000. Register an account, create a project and manuscript, then edit a section and save a revision. The [local reviewer setup](docs/local-setup.md#seed-a-sample-project) includes commands to create sample data.

### Run with Docker

```sh
docker run --rm -p 127.0.0.1:5000:5000 theseus:local
```

Open [http://localhost:5000](http://localhost:5000) in your browser. The container serves both the UI and API on that port. Stop the native server first if it already uses port 5000.

To use MongoDB or Gemini, configure `backend/.env` and pass it at runtime. Keep `PORT` unset or set to `5000` for this port mapping. Use a MongoDB address reachable from inside the container.

```sh
docker run --rm -p 127.0.0.1:5000:5000 --env-file backend/.env theseus:local
```

## Verification

From the repository root, activate the Python environment and run the lint checks and test suites.

```sh
npm run lint
npm --prefix frontend test
npm --prefix frontend run test:components
npm run test:backend
```

The local lint command runs ESLint, Ruff, and mypy. The [CI workflow](.github/workflows/ci.yml) runs the backend lint, format, and type checks through pre-commit and also runs `svelte-check` and Playwright. The backend integration tests may download the MiniLM model on first run.

## Team Roles

| Role | Team member |
| --- | --- |
| DevOps Engineer | Bernard Chua |
| AI Engineer | Patrick Salugsugan |
| Developer | Glen Rae Suguitan |
| Developer | Harvey Claur |
| Developer | Rhamy Catague |

## Tech Stack and Architecture

| Area | Technology |
| --- | --- |
| Frontend | Svelte and Vite |
| Backend | Flask REST API, served by Gunicorn in the production container |
| Storage | MongoDB for application records and Chroma for search vectors |
| AI | Gemini for configured embeddings, generation, and validation. MiniLM ONNX for embeddings in MongoDB mode without a Gemini key. |
| Delivery | GitHub Actions, Docker, and Render |

See the [architecture and database relationships](docs/architecture.md) and the [AI feature and evaluation write-up](docs/ai-feature.md).

## Production and Release

Theseus can be accessed on https://production-1l5a.onrender.com. See the [draft v1.0.0 changelog](CHANGELOG.md) and [deploy and rollback runbook](docs/deploy-and-rollback.md).

## DevOps and Delivery

- [Pipeline guide and diagram](docs/PIPELINE.md) and [pipeline operations](docs/pipeline-operations.md)
- [Deploy and rollback runbook](docs/deploy-and-rollback.md) and [maintenance and handover](docs/maintenance-and-handover.md)
- [Weekly pipeline metrics](docs/pipeline-metrics.md), [optimization log](docs/pipeline-optimization.md), and [incident log](docs/incident-log.md)

## API

Flask serves a session-authenticated REST API for accounts, projects, manuscripts, revisions, sources, and assistant conversations. See the [API reference](docs/api.md) for endpoints and request examples.

## Contributing

Pull requests are welcome. Ask questions, report bugs, or propose major changes in [GitHub Issues](https://github.com/b-chua-student/theseus/issues).

1. Create a short-lived branch from `main`, such as `feat/user-collections` or `fix/env-validation`.
2. Use Commitizen-style messages such as `feat(scope): message`. Update tests as appropriate and follow the [repository spec workflow](AGENTS.md) for behavior changes.
3. Open a PR and address reviewer feedback. Merge only after required checks pass and at least one teammate approves.
4. Delete the branch and verify the change in the deployed environment.

## License

The project lists [MIT](https://choosealicense.com/licenses/mit/) as its license. The repository license file and copyright attribution are pending confirmation.
