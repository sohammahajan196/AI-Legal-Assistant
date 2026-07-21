# FastAPI backend service image.
# See PLAN.md Section 13 and TASKS.md T51.
#
# Build (from repo root):
#   docker build -t ai-legal-backend ./backend
#
# Run (health check only — mount a built FAISS index for real chat traffic):
#   docker run --rm -p 8000:8000 \
#     -e GOOGLE_API_KEY=your-key \
#     -e BACKEND_API_TOKENS=dev-token:standard \
#     -v faiss_index:/app/data/faiss_index \
#     ai-legal-backend

FROM python:3.12-slim

WORKDIR /app

# Runtime libs for numpy / sentence-transformers wheels on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Dependency layer — cached separately from application code (deployment.mdc).
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Application code layer — changes here do not invalidate the pip layer above.
COPY app ./app
# Offline ingest/index-build CLIs (PLAN.md Section 13: docker compose run backend …).
COPY scripts ./scripts
COPY data/raw ./data/raw

# Bake the retrieval index into the image itself so the backend can serve
# traffic without a runtime volume — required on hosts with no persistent
# disk (e.g. Render's free tier). On docker-compose, an empty named volume
# mounted over data/faiss_index is auto-populated from this image content on
# first `up`, so this stays compatible with the existing volume-based flow.
# GOOGLE_API_KEY here is a build-time-only placeholder: these scripts never
# call Gemini, they only need Settings to pass its non-blank validation. The
# real key is supplied at runtime by the hosting platform's env vars, which
# override this image default.
ENV GOOGLE_API_KEY=build-time-placeholder
RUN python scripts/ingest.py && python scripts/build_index.py

# Writable data dirs; FAISS index is persisted via a named volume at runtime
# in docker-compose (pre-populated above for volume-less hosts).
RUN mkdir -p data/faiss_index data/bm25_index data/processed \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Named volume mount point for the offline-built FAISS index (PLAN.md Section 13).
# Recreate this volume after changing EMBEDDING_MODEL — a non-empty named volume
# keeps the previous index and will not pick up a newly baked image layer.
VOLUME ["/app/data/faiss_index"]

# Single worker only — embedding model + FAISS already dominate RAM on
# free-tier hosts (e.g. Render 512MB). Do not raise WEB_CONCURRENCY.
ENV WEB_CONCURRENCY=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"

# Explicit --workers 1 (uvicorn default is already 1; pin it so platforms
# cannot silently multi-process via an alternate start command).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
