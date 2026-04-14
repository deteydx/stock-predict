# syntax=docker/dockerfile:1.6

# ---------- Stage 1: build frontend ----------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: python runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libgomp is required by lightgbm; build-essential kept minimal and removed after install
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libgomp1 \
      curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps. Use editable install so __file__-based paths in
# stockpredict.api.app (which resolves frontend/dist relative to src) still work.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --upgrade pip \
 && pip install -e . \
 && apt-get purge -y --auto-remove build-essential \
 && rm -rf /root/.cache

# Copy remaining backend files (config/ is imported as a top-level package,
# so /app must be on sys.path — uvicorn's cwd handles that.)
COPY config ./config
COPY scripts ./scripts
ENV PYTHONPATH=/app

# Copy built frontend from stage 1 into expected path
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Runtime dirs (will be overridden by volumes in compose)
RUN mkdir -p /app/data /app/cache /app/reports /app/models

EXPOSE 8000

# NOTE: bind to 0.0.0.0 inside container; host only exposes 127.0.0.1:3002 via compose
CMD ["uvicorn", "stockpredict.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
