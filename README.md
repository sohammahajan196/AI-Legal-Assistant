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

Run the backend test suite with:

```bash
cd backend
pytest -q
```

## Setup (TODO - to be completed as part of TASKS.md T54)

- [ ] Backend local dev setup (`backend/`, Python virtualenv, `requirements.txt`)
- [ ] Frontend local dev setup (`frontend/`, Node, `npm install`)
- [ ] Data ingestion (`backend/scripts/ingest.py`) and index build (`backend/scripts/build_index.py`)
- [ ] Running the evaluation script (`backend/eval/run_eval.py`)
- [ ] Docker Compose usage (`docker compose up`)
- [ ] Required environment variables (see `.env.example`) and where to obtain the Gemini API key

## Project layout

See [STRUCTURE.md](./STRUCTURE.md) for the full annotated directory tree.
