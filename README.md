# AI Legal Assistant

An explainability-first, citation-grounded RAG assistant for Indian law. Every answer is
grounded in retrieved statutory text, cites its exact source, and carries a computed
confidence score.

> For full context, see: [PRD.md](./PRD.md) (what/why) - [PLAN.md](./PLAN.md) (architecture) -
> [TASKS.md](./TASKS.md) (implementation breakdown) - [STRUCTURE.md](./STRUCTURE.md) (repo layout).

## Status

Project scaffolding only. Folder/file structure is in place; business logic has not yet been
implemented. Follow `TASKS.md` for the dependency-ordered build plan, starting at Phase 0.

## Setup (TODO - to be completed as part of TASKS.md T54)

- [ ] Backend local dev setup (`backend/`, Python virtualenv, `requirements.txt`)
- [ ] Frontend local dev setup (`frontend/`, Node, `npm install`)
- [ ] Data ingestion (`backend/scripts/ingest.py`) and index build (`backend/scripts/build_index.py`)
- [ ] Running the evaluation script (`backend/eval/run_eval.py`)
- [ ] Docker Compose usage (`docker compose up`)
- [ ] Required environment variables (see `.env.example`) and where to obtain the Gemini API key

## Project layout

See [STRUCTURE.md](./STRUCTURE.md) for the full annotated directory tree.
