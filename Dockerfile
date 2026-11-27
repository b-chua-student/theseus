# Stage 1: build frontend
FROM node:24-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/bootstrap/rag.py bootstrap/rag.py
RUN python -m bootstrap.rag

COPY backend/ .
COPY --from=frontend /frontend/dist ./static

EXPOSE 5000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --access-logfile - --error-logfile - 'bootstrap.app:create_app()'"]
