# ============================================================
# Multi-stage Dockerfile for the Roadmap Tracker API
# Stage 1: builder - install dependencies into a venv
# Stage 2: runtime - slim image with only the venv + source
# ============================================================

# ---------- Stage 1: builder ----------
FROM python:3.13-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for asyncpg / bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Install dependencies into a venv so we can copy it cleanly to the runtime stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt requirements.lock.txt ./
RUN pip install -r requirements.lock.txt

# ---------- Stage 2: runtime ----------
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Runtime libs only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source (also mounted at runtime for dev, but baked in for prod builds)
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY roadmap.md ./roadmap.md

EXPOSE 8000

# Run as a non-root user in the production image.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Run migrations on container start, then launch uvicorn. The baked image
# never hot-reloads; docker-compose overrides the command to add --reload
# for local development.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]