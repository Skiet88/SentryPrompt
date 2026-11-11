# Production image for the SentryPrompt4 backend (NFR-004).
# Build context is backend/ (see render.yaml: dockerContext).

FROM python:3.11-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir uv

# Install dependencies first so code-only changes don't bust the layer cache.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT','8000') + '/health')"

# $PORT is set by the host (Render); default 8000 matches local dev.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
