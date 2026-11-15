# Stage 1: build the Svelte frontend into static files.
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: the Flask API, which also serves the built frontend from the same origin.
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY backend/ .
COPY --from=frontend /build/dist ./frontend_dist

# Run as an unprivileged user.
RUN useradd --create-home app && chown -R app /app
USER app

ENV FRONTEND_DIST=/app/frontend_dist \
    LOG_TO_STDOUT=1 \
    PYTHONUNBUFFERED=1

# Render supplies PORT (default 10000).
#
# Exactly ONE worker, deliberately: the vector store, event bus and rate-limit
# counters are held in process memory, so a second worker would have its own empty
# copy (chat could not see what another worker indexed). Threads give concurrency
# for slow AI calls without that problem.
CMD ["sh", "-c", "exec gunicorn run:app --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 8 --timeout 90 --access-logfile -"]
