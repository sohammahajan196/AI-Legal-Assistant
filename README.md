# AI Legal Assistant

An explainability-first, citation-grounded RAG assistant for Indian law. Every answer is
grounded in retrieved statutory text, cites its exact source, and carries a computed
confidence score.

> For full context, see: [PRD.md](./PRD.md) (what/why) - [PLAN.md](./PLAN.md) (architecture) -
> [TASKS.md](./TASKS.md) (implementation breakdown) - [STRUCTURE.md](./STRUCTURE.md) (repo layout).

## Status

Project scaffolding only. Folder/file structure is in place; business logic has not yet been
implemented. Follow `TASKS.md` for the dependency-ordered build plan, starting at Phase 0.

## Backend Quick Start (Phase 0)

Minimal steps to boot the FastAPI skeleton (TASKS.md T02/T03). A comprehensive setup guide
(ingestion, index build, Docker Compose, all env vars) lands with T54.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # Windows: copy ..\.env.example .env
# then edit .env and set a real GOOGLE_API_KEY - the app refuses to start without one
uvicorn app.main:app --reload
```

Then visit `http://127.0.0.1:8000/` — it should return `{"name": "AI Legal Assistant API", "status": "ok"}`,
and the terminal should show a structured JSON log line for `application_startup`.

`GOOGLE_API_KEY` is validated at startup (`app/core/config.py`) — a missing or blank value
raises a clear error immediately instead of booting into a broken state (TASKS.md T03).

## Backend Testing (Phase 0)

The test harness uses `pytest` + `pytest-asyncio` (TASKS.md T04). From `backend/` with your
virtualenv activated:

```bash
# CI-style quiet run (recommended for local checks and CI)
pytest -q

# Verbose output with per-test names
pytest -v

# Run only the harness smoke tests (sync + async)
pytest tests/test_harness.py -v
```

Expected: all tests pass (including a trivial sync test and an async `pytest-asyncio` example
in `tests/test_harness.py`). No real network calls, Gemini API key, or Redis instance is
required — `tests/conftest.py` supplies safe test defaults.

To (re)generate criminal-domain raw corpus files (TASKS.md T05):

```bash
cd backend
python scripts/curate_criminal.py
pytest tests/test_corpus_criminal.py -v
```

To (re)generate civil-domain raw corpus files (TASKS.md T06):

```bash
cd backend
python scripts/curate_civil.py
pytest tests/test_corpus_civil.py -v
```

To (re)generate family-domain raw corpus files (TASKS.md T07):

```bash
cd backend
python scripts/curate_family.py
pytest tests/test_corpus_family.py -v
```

To (re)generate labour-domain raw corpus files (TASKS.md T08):

```bash
cd backend
python scripts/curate_labour.py
pytest tests/test_corpus_labour.py -v
```

To (re)generate consumer-domain raw corpus files (TASKS.md T09):

```bash
cd backend
python scripts/curate_consumer.py
pytest tests/test_corpus_consumer.py -v
```

To (re)generate property-domain raw corpus files (TASKS.md T10):

```bash
cd backend
python scripts/curate_property.py
pytest tests/test_corpus_property.py -v
```

## Corpus ingestion and index build (Phase 2–3)

After raw act texts exist under `backend/data/raw/<domain>/`, run the full offline
pipeline from `backend/` with your virtualenv activated:

```bash
# 1. Parse raw acts into processed JSONL chunks (TASKS.md T12)
python scripts/ingest.py

# 2. QA pass over processed chunks — exits non-zero on issues (TASKS.md T13)
python scripts/validate_corpus.py

# 3. Validate + build FAISS and BM25 indices in one command (TASKS.md T17)
python scripts/build_index.py
```

Step 3 runs corpus validation first and **aborts without writing indices** if
validation fails. On success it writes:

- `data/faiss_index/` — semantic FAISS index (TASKS.md T15)
- `data/bm25_index/` — keyword BM25 index (TASKS.md T16)

The first FAISS build downloads the HuggingFace embedding model
(`EMBEDDING_MODEL`, default `BAAI/bge-base-en-v1.5`) — allow a few minutes on a
fresh machine. BM25 build is fast.

Index output paths are configurable via `FAISS_INDEX_DIR` and `BM25_INDEX_DIR` in
`.env` (see `.env.example`).

## Setup (TODO - to be completed as part of TASKS.md T54)

- [ ] Backend local dev setup (`backend/`, Python virtualenv, `requirements.txt`)
- [ ] Frontend local dev setup (`frontend/`, Node, `npm install`)
- [ ] Data ingestion (`backend/scripts/ingest.py`) and index build (`backend/scripts/build_index.py`) — see **Corpus ingestion and index build** above
- [ ] Running the evaluation script (`backend/eval/run_eval.py`)
- [ ] Docker Compose usage (`docker compose up`)
- [ ] Required environment variables (see `.env.example`) and where to obtain the Gemini API key

## Project layout

See [STRUCTURE.md](./STRUCTURE.md) for the full annotated directory tree.
