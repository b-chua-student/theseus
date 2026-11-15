# Setup Guide

## Prerequisites

| Tool    | Version | Notes                                                     |
| ------- | ------- | --------------------------------------------------------- |
| Node.js | 20+     | Frontend build and the `npm run dev` runner               |
| Python  | 3.12+   | Backend                                                   |
| MongoDB | any     | Local (`mongodb://localhost:27017`) or MongoDB Atlas      |
| Gemini API key | -| Needed for the AI assistant. Without it, chat returns 503 |

## 1. Install

```bash
git clone https://github.com/b-chua-student/theseus
cd theseus
npm install            # root deps + (postinstall) frontend deps
```

Create and activate a virtual environment, then install the backend packages:

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate      # fish: activate.fish, Windows: Scripts\activate
pip install -r backend/requirements.txt
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

`requirements.txt` includes dev tooling (pytest, mypy, ruff hooks, etc.) on top of
`requirements-prod.txt`, which is all a deployed image needs.

## 2. Configure

```bash
cp backend/.env.example backend/.env
```

| Variable               | Required | Default                      | Purpose                                              |
| ---------------------- | -------- | ---------------------------- | ---------------------------------------------------- |
| `SECRET_KEY`           | yes      | -                            | Signs session cookies. The server refuses to start without it. |
| `GEMINI_API_KEY`       | for chat | -                            | Google Gemini access                                 |
| `MONGODB_URI`          | no       | `mongodb://localhost:27017`  | MongoDB connection string                            |
| `MONGODB_DB`           | no       | `mydb`                       | Database name                                        |
| `CHROMA_PERSIST_PATH`  | no       | `./chroma_data`              | ChromaDB path (adapter exists but is not wired in yet) |
| `GIT_REPO_DIR`         | no       | `./repository`               | Dulwich repository directory                         |
| `CHUNK_SIZE`           | no       | `512`                        | Chunk size for document indexing                     |

Production-only variables:

| Variable                | Purpose                                                       |
| ----------------------- | ------------------------------------------------------------- |
| `SESSION_COOKIE_SECURE` | Set to `1` to send the session cookie only over HTTPS         |
| `TRUST_PROXY_HOPS`      | Number of reverse proxies in front of the app (1 on Render)   |
| `LOG_TO_STDOUT`         | Set to `1` to log to the console instead of `logs/app.log`    |
| `FRONTEND_DIST`         | Path to the built frontend; Flask serves it from the same origin |

## 3. Run

Make sure MongoDB is running, the virtual environment is active, and you are in the repository root:

```bash
npm run dev
```

This starts both servers:

- Frontend (Vite): http://localhost:5173. It proxies `/api` to the backend.
- Backend (Flask): http://localhost:5000. Health check: `GET /healthz`.

To run them separately:

```bash
npm --prefix frontend run dev
python backend/run.py
```

## 4. Test and lint

```bash
npm run test:backend      # pytest (uses in-memory adapters; no MongoDB or Gemini needed)
npm run lint              # eslint + ruff + mypy
npm run format:backend    # ruff format
npm run fix:backend       # ruff --fix
```

## 5. Deploy

The repository ships a multi-stage `Dockerfile` (builds the Svelte app, then serves it and the API from one Flask/Gunicorn process) and a Render blueprint (`render.yaml`).

```bash
docker build -t theseus .
docker run -p 10000:10000 \
  -e SECRET_KEY=... -e MONGODB_URI=... -e GEMINI_API_KEY=... theseus
```

On Render: **New > Blueprint**, select the repository, and enter `MONGODB_URI` and `GEMINI_API_KEY` when prompted. `SECRET_KEY` is generated for you.

The container runs exactly **one Gunicorn worker** (with 8 threads) on purpose. The vector store, event bus and rate-limit counters live in process memory, so extra workers would each hold their own empty copy.

## Troubleshooting

| Symptom                                   | Cause / fix                                                              |
| ----------------------------------------- | ------------------------------------------------------------------------ |
| `RuntimeError: SECRET_KEY is not set`     | Set `SECRET_KEY` in `backend/.env`                                       |
| Chat returns `503`                        | `GEMINI_API_KEY` is missing or invalid                                   |
| Chat returns `429`                        | Gemini is rate limiting; retry after the `Retry-After` interval          |
| Login/register returns `429`              | Auth endpoints allow 5 requests per minute per IP                        |
| Connection errors on startup              | MongoDB is not reachable at `MONGODB_URI`                                |
| Logged out immediately in production      | `SESSION_COOKIE_SECURE=1` requires HTTPS                                 |
