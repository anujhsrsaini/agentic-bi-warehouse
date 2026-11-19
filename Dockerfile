# syntax=docker/dockerfile:1.7

# ---------- Stage 1: build the React/Vite frontend ----------
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN rm -f tsconfig.tsbuildinfo && npm run build

# ---------- Stage 2: Python runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/home/appuser \
    AGENTIC_BI_DUCKDB_THREADS=2 \
    AGENTIC_BI_DUCKDB_MEMORY_LIMIT=1GB \
    AGENTIC_BI_DUCKDB_SANDBOX_ENABLED=true \
    AGENTIC_BI_CACHE_DIR=/app/.cache

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py run_app.py ./
COPY src ./src
COPY config ./config
COPY data/seed ./data/seed
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/.cache \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "api:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers", \
     "--forwarded-allow-ips=*", \
     "--limit-concurrency", "8"]
