FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "api.app:create_app()"]
