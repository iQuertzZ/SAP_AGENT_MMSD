# ── Build arguments (injected by CI) ─────────────────────────────────────────
ARG BUILD_DATE="unknown"
ARG GIT_SHA="unknown"
ARG VERSION="1.0.0"

# ── Stage 1: builder ──────────────────────────────────────────────────────────
# python:3.11-slim (not alpine) — asyncpg requires gcc at build time
FROM python:3.14-slim AS builder

WORKDIR /app

# System packages needed to compile asyncpg and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Isolated virtual environment (keeps runtime stage clean)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies first (cached unless requirements.txt changes)
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn>=21.0

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS runtime

ARG BUILD_DATE="unknown"
ARG GIT_SHA="unknown"
ARG VERSION="1.0.0"

# OCI image labels
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.source="https://github.com/iQuertzZ/SAP_AGENT_MMSD"
LABEL org.opencontainers.image.title="SAP MM/SD AI Copilot"
LABEL org.opencontainers.image.description="Enterprise-grade AI Copilot for SAP MM/SD modules"

# Runtime-only system packages (curl for HEALTHCHECK, libpq for asyncpg at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root user (UID 1001)
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy compiled venv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GIT_SHA="${GIT_SHA}" \
    APP_VERSION="${VERSION}"

# Copy application source (owned by appuser)
COPY --chown=appuser:appgroup . .

# Pre-create pytest cache dir so appuser can write to it during docker-test
RUN mkdir -p /app/.pytest_cache && chown appuser:appgroup /app/.pytest_cache

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
