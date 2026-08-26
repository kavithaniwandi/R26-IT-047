# ============================================================
# Dockerfile — Disaster Relief Backend (FastAPI + MySQL)
# Multi-stage build: slim production image
# ============================================================

# Stage 1: Base
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev \
        pkg-config \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS dependencies

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM dependencies AS app

COPY . .

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
