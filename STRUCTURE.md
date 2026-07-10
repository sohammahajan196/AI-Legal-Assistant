# Project Folder Structure

This document lays out the full repository layout implied by [PLAN.md](./PLAN.md), [PRD.md](./PRD.md), and [TASKS.md](./TASKS.md), with an explanation of every folder and major file. Nothing here has been created on disk yet — this is the reference structure to scaffold when implementation starts.

```
AI Legal Assistant/
├── PLAN.md
├── PRD.md
├── TASKS.md
├── STRUCTURE.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── .cursor/
│   └── rules/
│       ├── general.mdc
│       ├── backend.mdc
│       ├── frontend.mdc
│       ├── database.mdc
│       ├── testing.mdc
│       └── deployment.mdc
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── chat.py
│   │   │       ├── sessions.py
│   │   │       ├── domains.py
│   │   │       └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── logging.py
│   │   │   └── rate_limit.py
│   │   ├── rag/
│   │   │   ├── chunking.py
│   │   │   ├── embeddings.py
│   │   │   ├── vectorstore.py
│   │   │   ├── bm25_index.py
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── llm.py
│   │   │   ├── structured_llm.py
│   │   │   ├── confidence.py
│   │   │   ├── refusal.py
│   │   │   ├── prompts.py
│   │   │   ├── condense.py
│   │   │   ├── chain.py
│   │   │   └── cache.py
│   │   ├── schemas/
│   │   │   ├── legal_answer.py
│   │   │   └── chat.py
│   │   └── services/
│   │       ├── chat_service.py
│   │       ├── session_store.py
│   │       └── query_log.py
│   ├── scripts/
│   │   ├── ingest.py
│   │   ├── validate_corpus.py
│   │   └── build_index.py
│   ├── data/
│   │   ├── raw/
│   │   │   ├── criminal/
│   │   │   ├── civil/
│   │   │   ├── family/
│   │   │   ├── labour/
│   │   │   ├── consumer/
│   │   │   └── property/
│   │   ├── processed/
│   │   ├── faiss_index/
│   │   └── app.db
│   ├── eval/
│   │   ├── qa_dataset.jsonl
│   │   ├── run_eval.py
│   │   └── results/
│   └── tests/
│       ├── test_chunking.py
│       ├── test_retrieval.py
│       ├── test_structured_llm.py
│       ├── test_confidence.py
│       ├── test_chain.py
│       └── test_api.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx
    │   └── api/
    │       ├── chat/
    │       │   └── route.ts
    │       └── sessions/
    │           └── [id]/route.ts
    ├── components/
    │   ├── ChatWindow.tsx
    │   ├── MessageBubble.tsx
    │   ├── CitationCard.tsx
    │   ├── ConfidenceBadge.tsx
    │   ├── DisclaimerBanner.tsx
    │   └── UserTypeSelector.tsx
    └── lib/
        └── apiClient.ts
```

---

## Root level

- **`PLAN.md`** — the technical architecture: domain list, ingestion/chunking design, hybrid retrieval, RAG orchestration, schemas, confidence scoring, API/frontend/deployment design. The source of truth for *how* the system is built.
- **`PRD.md`** — the product requirements: problem statement, goals, personas, user stories, functional/non-functional requirements, success metrics, risks. The source of truth for *what* and *why*.
- **`TASKS.md`** — the 54-task, dependency-ordered implementation breakdown with acceptance criteria. The source of truth for *in what order* and *how to verify each step*.
- **`STRUCTURE.md`** — this file; keeps the intended repo layout explicit and reviewable before any scaffolding happens.
- **`README.md`** — the entry point for a new developer: setup instructions, how to run ingestion/index-build, how to run locally vs. via Docker, links to the three docs above (T54 in `TASKS.md`).
- **`.env.example`** — documents every required environment variable (Gemini API key, bearer tokens, Redis URL, confidence thresholds) without real secret values — the only env file that gets committed.
- **`.gitignore`** — excludes `.env`, `data/faiss_index/`, `data/app.db`, `node_modules/`, Python virtualenvs/`__pycache__`, and other build artifacts from version control.
- **`docker-compose.yml`** — wires the `backend`, `frontend`, and `redis` services together for one-command local/demo deployment (PLAN.md §13, T53).

## `.cursor/rules/`

Persistent AI-agent guidance so implementation stays consistent with the architecture without re-explaining it every session:

- **`general.mdc`** — always-applied non-negotiables: grounding, citation integrity, computed confidence, refusal-over-guessing, disclaimers.
- **`backend.mdc`**, **`frontend.mdc`**, **`database.mdc`**, **`testing.mdc`**, **`deployment.mdc`** — scoped conventions for each concern, applied automatically when matching files are open.

## `backend/` — FastAPI + LangChain RAG service

- **`Dockerfile`** — builds the backend service image (T51).
- **`requirements.txt`** — pinned Python dependencies (fastapi, uvicorn, langchain, langchain-google-genai, langchain-huggingface, faiss-cpu, rank-bm25, pydantic, redis, slowapi, pytest, etc.).
- **`pytest.ini`** — test discovery/config so `pytest` works from the `backend/` root (T04).

### `backend/app/` — application code

- **`main.py`** — FastAPI app instantiation, router registration, startup/shutdown hooks (e.g. loading the FAISS/BM25 indices once at boot) (T02).

#### `app/api/routes/` — HTTP layer only

- **`chat.py`** — `POST /api/v1/chat`, the main Q&A endpoint; wires auth → rate limit → `chat_service` → logging (T37).
- **`sessions.py`** — `GET /api/v1/sessions/{id}/history` (T38).
- **`domains.py`** — `GET /api/v1/domains`, lists the 6 supported legal domains for the frontend selector (T39).
- **`health.py`** — `GET /api/v1/health`, unauthenticated liveness check (T39).

Exists as its own layer so HTTP concerns (status codes, request/response shapes) never leak retrieval/prompt logic — that all lives in `rag/`/`services/` (enforced by `backend.mdc`).

#### `app/core/` — cross-cutting infrastructure

- **`config.py`** — `pydantic-settings`-based settings object; the single place env vars are read (T03).
- **`security.py`** — bearer-token auth dependency, token→tier mapping (T34).
- **`logging.py`** — structured JSON logging setup (T03).
- **`rate_limit.py`** — Redis-backed per-token rate limiting via `slowapi` (T35).

#### `app/rag/` — the RAG pipeline itself

This is the heart of the system — every module maps directly to a pipeline stage in PLAN.md §3-§7:

- **`chunking.py`** — section-boundary regex parser + metadata extractor; turns raw act text into citable chunks (T11).
- **`embeddings.py`** — HuggingFace embedding model wrapper (`BAAI/bge-base-en-v1.5`) (T14).
- **`vectorstore.py`** — FAISS index build/query, domain-filterable (T15).
- **`bm25_index.py`** — BM25 keyword index build/query (T16).
- **`hybrid_retriever.py`** — `EnsembleRetriever` combining FAISS + BM25 via Reciprocal Rank Fusion (T18).
- **`reranker.py`** — optional cross-encoder re-ranking stage, config-gated (T19).
- **`llm.py`** — `ChatGoogleGenerativeAI` client wrapper (T22).
- **`structured_llm.py`** — `.with_structured_output(...)` call + bounded retry-with-repair on validation failure (T23).
- **`confidence.py`** — computes `confidence_score` from retrieval + groundedness signals, never from LLM self-report (T25).
- **`refusal.py`** — pre- and post-generation refusal/fallback decision logic and canned templates (T26).
- **`prompts.py`** — per-`user_type` prompt templates with the disclaimer baked in (T27).
- **`condense.py`** — rewrites multi-turn follow-ups into standalone queries (T29).
- **`chain.py`** — assembles every stage above into the final LCEL RAG chain (T30).
- **`cache.py`** — Redis exact-match cache + semantic near-duplicate query cache (T32).

Exists as a dedicated package (separate from `api/` and `services/`) because it's the most complex, most-tested, and most architecturally significant part of the system — isolating it makes each stage independently unit-testable, per `TASKS.md`'s "independently buildable" requirement.

#### `app/schemas/` — Pydantic v2 contracts

- **`legal_answer.py`** — `LegalDomain` enum, `LLMStructuredAnswer` (what the LLM must return), `SourceCitation`, `LegalAnswerResponse` (the final API contract) (T21). Kept separate from the LLM client code so the contract can be reasoned about/tested independently of any model.
- **`chat.py`** — request/response models for the FastAPI endpoints (e.g. `ChatRequest` with `query`, `session_id`, `user_type`, `consent_to_log`).

#### `app/services/` — orchestration glue between API and RAG core

- **`chat_service.py`** — the single entrypoint the API layer calls: checks cache → invokes the RAG chain → stores cache → returns response (T33).
- **`session_store.py`** — SQLite-backed session/message CRUD for multi-turn history (T28).
- **`query_log.py`** — consent-aware audit logging to the `query_logs` table (T36).

Exists to keep `api/routes/` thin and `rag/` focused purely on RAG logic — `services/` is where request-scoped orchestration (caching, logging, session lookups) happens.

### `backend/scripts/` — offline/operational CLIs (never exposed over HTTP)

- **`ingest.py`** — raw act text → processed, chunked, metadata-tagged JSONL per domain (T12).
- **`validate_corpus.py`** — QA pass over processed chunks (no empty sections, no missing metadata) (T13).
- **`build_index.py`** — runs validation then builds both the FAISS and BM25 index artifacts in one command (T17).

Kept as CLI scripts rather than API endpoints deliberately (per PLAN.md §3) — rebuilding the corpus/index is an infrequent, trusted-operator action, not something to expose to end users.

### `backend/data/` — corpus and generated artifacts

- **`raw/<domain>/`** — one folder per legal domain, containing the curated bare-act text files (IPC/CrPC, CPC, HMA/SMA, ID Act/Code on Wages, CPA 2019, TPA 1882) sourced from India Code (T05-T10). Treated as immutable input.
- **`processed/`** — one JSONL file per domain, the output of `ingest.py`; each line is one citable chunk with metadata.
- **`faiss_index/`** — the persisted FAISS index, mounted as a Docker volume so it survives container restarts.
- **`app.db`** — the SQLite database file backing `sessions`, `messages`, and `query_logs`.

### `backend/eval/` — offline quality measurement (not part of the live API)

- **`qa_dataset.jsonl`** — 30-50 hand-written Q&A pairs spanning all 6 domains with expected domain/section references (T48).
- **`run_eval.py`** — computes retrieval precision/recall@k and answer-correctness against the dataset, producing a report (T49-T50).
- **`results/`** — generated report output (e.g. `retrieval_report.json`), so eval runs are comparable over time.

### `backend/tests/` — automated test suite

One file per major concern (chunking, retrieval, structured output, confidence, the full chain, the API layer) so a failure immediately localizes to the responsible module, mirroring the `rag/` package split (T20, T24, T29, T31, T40).

## `frontend/` — Next.js 15 chat UI

- **`Dockerfile`** — builds the production Next.js standalone image (T52).
- **`package.json`**, **`next.config.js`**, **`tailwind.config.ts`** — project/build configuration.

### `frontend/app/`

- **`layout.tsx`** — root layout; a natural place for the always-visible `DisclaimerBanner`.
- **`page.tsx`** — the chat page itself: message list, input, `user_type` selector (T43, T46).
- **`api/chat/route.ts`** — server-side proxy to the FastAPI backend; the only place the backend bearer token is read from env (T42). Exists specifically so the token never reaches client-side JavaScript.
- **`api/sessions/[id]/route.ts`** — proxies session history retrieval the same way.

### `frontend/components/`

- **`ChatWindow.tsx`** — top-level chat container composing the message list and input.
- **`MessageBubble.tsx`** — renders a single user or assistant message.
- **`CitationCard.tsx`** — renders one `SourceCitation` (document, section, excerpt, score) (T44).
- **`ConfidenceBadge.tsx`** — color-coded confidence indicator using the same thresholds as the backend's refusal logic (T44).
- **`DisclaimerBanner.tsx`** — the persistent legal disclaimer + consent checkbox (T45).
- **`UserTypeSelector.tsx`** — layperson/law-student/lawyer selector feeding `user_type` into requests (T46).

Exists as small, single-responsibility components (rather than one large page file) so citation/confidence rendering can be unit-tested in isolation, per `testing.mdc`.

### `frontend/lib/`

- **`apiClient.ts`** — a thin wrapper around calls to the `/api/chat` and `/api/sessions/*` proxy routes, keeping fetch/error-handling logic out of components.

---

Nothing above has been created on disk — this is the reference layout for when scaffolding begins (starting with `TASKS.md` Phase 0). Let me know if you'd like me to actually scaffold these folders/empty files next (that would require switching out of Plan mode).
