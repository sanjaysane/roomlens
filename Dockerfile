# ── RoomLens: WhatsApp-first room visualization ─────────────────────
# Multi-stage build: dependencies in one layer, non-root runtime.
# ffmpeg is included for video frame extraction / Ken Burns clips.

FROM python:3.14-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
RUN apt-get update -qq \
    && apt-get install -y -qq --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

FROM base AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY src/ ./src/
COPY locales/ ./locales/
COPY sql/ ./sql/
# Non-root user for production.
RUN useradd --create-home --shell /bin/false appuser \
    && mkdir -p /app/data/media \
    && chown -R appuser:appuser /app
USER appuser
ENV MEDIA_DIR=/app/data/media
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
