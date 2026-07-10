# Implementation Task Breakdown

Derived from [PRD.md](./PRD.md) and [PLAN.md](./PLAN.md). 54 tasks, ordered so that each task only depends on tasks with a lower ID. Each task is independently buildable/testable in isolation (using stubs/fixtures/mocks where a real upstream dependency doesn't exist yet).

---

## Phase 0 — Project Foundation

### T01 — Initialize monorepo repository structure
**Depends on:** —
**Description:** Create the top-level `backend/` and `frontend/` directories, root `.gitignore`, root `README.md` stub, and `.env.example` placeholder.
**Acceptance Criteria:**
- Repo has `backend/`, `frontend/` folders and root `.gitignore` covering Python/Node artifacts, `.env`, `data/faiss_index/`.
- `README.md` exists with a one-paragraph project description.
- Running `git status` shows a clean tree after initial commit (no stray untracked build artifacts).

### T02 — Backend service skeleton (FastAPI app boots)
**Depends on:** T01
**Description:** Create `backend/app/main.py` with a minimal FastAPI app and a `/` route, plus `requirements.txt`/`pyproject.toml` with core deps (fastapi, uvicorn).
**Acceptance Criteria:**
- `uvicorn app.main:app` starts without error and `GET /` returns 200.
- `requirements.txt` pins at least fastapi, uvicorn, pydantic.
- Project runs in a fresh virtualenv following README instructions.

### T03 — Backend configuration & logging setup
**Depends on:** T02
**Description:** Add `app/core/config.py` using `pydantic-settings` to load env vars (API keys, model names, thresholds, Redis/SQLite paths), and `app/core/logging.py` for structured JSON logging.
**Acceptance Criteria:**
- `Settings()` object loads defaults and overrides from a `.env` file.
- Missing required secrets (e.g. `GOOGLE_API_KEY`) raise a clear startup error, not a silent None.
- A log line emitted at startup appears in structured (JSON) format with timestamp and level.

### T04 — Backend test framework setup
**Depends on:** T02
**Description:** Add `pytest`, `pytest-asyncio`, a `tests/` folder, and a trivial passing test to confirm the harness works end-to-end.
**Acceptance Criteria:**
- `pytest` run from `backend/` discovers and passes at least one test.
- CI-style command (e.g. `pytest -q`) documented in README.
- Async test example passes using `pytest-asyncio`.

---

## Phase 1 — Legal Corpus Sourcing

### T05 — Curate Criminal domain raw texts (IPC 1860 + CrPC 1973)
**Depends on:** T01
**Description:** Download/export official bare-act text for IPC and CrPC from India Code, convert to clean UTF-8 `.txt`, and save to `backend/data/raw/criminal/`.
**Acceptance Criteria:**
- Two text files exist under `backend/data/raw/criminal/` with consistent section header formatting (e.g. `Section 304A.`).
- Manual spot-check of 5 random sections confirms text matches the official source with no OCR/formatting corruption.
- A short `SOURCES.md` note records the source URL and retrieval date per file.

### T06 — Curate Civil domain raw texts (CPC 1908)
**Depends on:** T01
**Description:** Same curation process as T05, applied to the Code of Civil Procedure, 1908, saved to `backend/data/raw/civil/`.
**Acceptance Criteria:**
- Same as T05, scoped to `civil/` domain folder and CPC source.

### T07 — Curate Family domain raw texts (HMA 1955 + SMA 1954)
**Depends on:** T01
**Description:** Same curation process, applied to Hindu Marriage Act 1955 and Special Marriage Act 1954, saved to `backend/data/raw/family/`.
**Acceptance Criteria:**
- Same as T05, scoped to `family/` domain folder and both source acts.

### T08 — Curate Labour domain raw texts (Industrial Disputes Act 1947 + Code on Wages 2019)
**Depends on:** T01
**Description:** Same curation process, saved to `backend/data/raw/labour/`.
**Acceptance Criteria:**
- Same as T05, scoped to `labour/` domain folder and both source acts.

### T09 — Curate Consumer domain raw texts (Consumer Protection Act 2019)
**Depends on:** T01
**Description:** Same curation process, saved to `backend/data/raw/consumer/`.
**Acceptance Criteria:**
- Same as T05, scoped to `consumer/` domain folder.

### T10 — Curate Property domain raw texts (Transfer of Property Act 1882)
**Depends on:** T01
**Description:** Same curation process, saved to `backend/data/raw/property/`.
**Acceptance Criteria:**
- Same as T05, scoped to `property/` domain folder.

---

## Phase 2 — Parsing & Chunking

### T11 — Section-boundary parser + metadata extractor
**Depends on:** T05 (any one curated file needed to develop/test against)
**Description:** Build `backend/app/rag/chunking.py`: a regex-based parser that splits a raw act text into per-section chunks and attaches metadata (`domain`, `act_name`, `act_year`, `chapter`, `section_number`, `section_title`, `source_citation`).
**Acceptance Criteria:**
- Unit test parses a sample IPC excerpt into the correct number of section chunks with correct section numbers extracted.
- Long sections are further split on sub-clauses `(1)`, `(2)` when the section exceeds a configurable length threshold.
- Every output chunk has all required metadata fields populated (no `None`/empty section_number).

### T12 — Ingestion CLI (raw texts → processed chunk JSONL)
**Depends on:** T05, T06, T07, T08, T09, T10, T11
**Description:** Build `backend/scripts/ingest.py` that walks `data/raw/<domain>/*.txt`, runs the T11 parser, and writes `data/processed/<domain>.jsonl` (one chunk per line).
**Acceptance Criteria:**
- Running `python scripts/ingest.py` processes all 6 domain folders and produces 6 non-empty JSONL files.
- Each JSONL line is valid JSON matching the chunk schema from T11.
- Re-running the script is idempotent (overwrites cleanly, no duplicate/appended chunks).

### T13 — Corpus QA/validation script
**Depends on:** T12
**Description:** Build `backend/scripts/validate_corpus.py` that checks processed chunks for empty text, duplicate section numbers within an act, and missing metadata, and prints a summary report.
**Acceptance Criteria:**
- Script exits non-zero and lists offending chunks if any required field is empty.
- Script reports total chunk count per domain.
- Running against the current corpus (post-T12) exits zero (clean).

---

## Phase 3 — Embeddings & Indexing

### T14 — HuggingFace embedding wrapper
**Depends on:** T03
**Description:** Build `backend/app/rag/embeddings.py` wrapping `HuggingFaceEmbeddings` (`BAAI/bge-base-en-v1.5`) behind a config-driven factory function.
**Acceptance Criteria:**
- `get_embedding_model()` returns a working embedder; embedding a sample sentence returns a vector of the expected dimension.
- Model name is overridable via settings/env without code changes.
- Unit test confirms two similar sentences have higher cosine similarity than two unrelated ones.

### T15 — FAISS index module (build + query, domain-filterable)
**Depends on:** T12, T14
**Description:** Build `backend/app/rag/vectorstore.py` with functions to build a FAISS index from processed JSONL chunks and to query it with an optional `domain` metadata filter, persisting to `data/faiss_index/`.
**Acceptance Criteria:**
- Building the index from the T12 output succeeds and writes index files to disk.
- Reloading the persisted index and querying a known phrase returns the section it came from in the top results.
- Querying with a `domain` filter excludes chunks from other domains.

### T16 — BM25 index module (build + query)
**Depends on:** T12
**Description:** Build `backend/app/rag/bm25_index.py` wrapping `BM25Retriever` over the same processed chunks, with build/persist/load functions.
**Acceptance Criteria:**
- Building the BM25 index from T12 output succeeds.
- A query containing an exact section number/keyword (e.g. "304A") returns the corresponding chunk in the top results.
- Index can be serialized and reloaded without rebuilding from scratch.

### T17 — Unified build_index CLI entrypoint
**Depends on:** T13, T15, T16
**Description:** Build `backend/scripts/build_index.py` that runs corpus validation (T13) then builds both FAISS (T15) and BM25 (T16) indices in one command.
**Acceptance Criteria:**
- Single command `python scripts/build_index.py` produces both index artifacts from a clean checkout (given raw data + ingestion already run).
- Script aborts with a clear error if corpus validation (T13) fails.
- README documents the full "ingest → validate → build index" sequence.

---

## Phase 4 — Hybrid Retrieval

### T18 — EnsembleRetriever (RRF fusion) + score normalization
**Depends on:** T15, T16
**Description:** Build `backend/app/rag/hybrid_retriever.py` combining the FAISS and BM25 retrievers via LangChain's `EnsembleRetriever`, plus a utility to min-max normalize fused scores to `[0,1]`.
**Acceptance Criteria:**
- Given a query with both a semantic paraphrase match and an exact-keyword match, the fused top-K contains both relevant chunks.
- Fusion weights (semantic vs. keyword) are configurable.
- Unit test confirms normalized scores fall within `[0,1]` for a range of raw score inputs.

### T19 — Optional cross-encoder reranker module
**Depends on:** T18
**Description:** Build `backend/app/rag/reranker.py` wrapping a HuggingFace cross-encoder (`ms-marco-MiniLM-L-6-v2`) via `ContextualCompressionRetriever`, gated by an `ENABLE_RERANKER` config flag.
**Acceptance Criteria:**
- With the flag enabled, reranking a fused candidate set reorders results and returns the configured top-N.
- With the flag disabled, the hybrid retriever's output passes through unchanged.
- Unit test with a synthetic query/candidate set confirms the most relevant candidate is ranked first after reranking.

### T20 — Retrieval integration test (fixture corpus)
**Depends on:** T18, T19
**Description:** Build a small fixture corpus (~10-15 hand-written chunks across 2-3 domains) and an integration test proving hybrid retrieval outperforms either single method alone on a fixed query set.
**Acceptance Criteria:**
- Test builds fixture FAISS+BM25 indices in-memory/temp-dir (no dependency on the real corpus).
- Test asserts hybrid retrieval recall@5 ≥ max(semantic-only, keyword-only recall@5) on the fixture query set.
- Test runs in under a few seconds as part of the standard test suite.

---

## Phase 5 — Structured LLM Output

### T21 — Pydantic v2 schemas
**Depends on:** T03
**Description:** Build `backend/app/schemas/legal_answer.py` defining `LegalDomain` (enum), `LLMStructuredAnswer`, `SourceCitation`, and `LegalAnswerResponse` per PLAN.md §6.
**Acceptance Criteria:**
- All models validate successfully with representative sample data.
- `confidence_score` field rejects values outside `[0,1]`.
- `LegalDomain` enum contains exactly the 6 domains plus `other`.

### T22 — Gemini LLM client wrapper
**Depends on:** T03
**Description:** Build `backend/app/rag/llm.py` wrapping `ChatGoogleGenerativeAI` with model name/temperature from config, exposing sync and async invocation.
**Acceptance Criteria:**
- Wrapper successfully returns a completion for a trivial prompt against a real API key (manual/integration test, skipped in CI if no key present).
- Model name and temperature are configurable via settings, not hardcoded.
- Async `ainvoke` path is covered by at least one test using a mocked client.

### T23 — Structured-output call + retry-with-repair wrapper
**Depends on:** T21, T22
**Description:** Build `backend/app/rag/structured_llm.py` implementing `.with_structured_output(LLMStructuredAnswer, method="json_schema")` plus a bounded retry loop (max 2 retries) that re-prompts with the validation error on failure.
**Acceptance Criteria:**
- Given a mocked LLM that returns invalid JSON on the first call and valid JSON on the second, the wrapper returns the valid parsed result without raising.
- After exceeding max retries, the wrapper raises a well-defined exception rather than hanging or silently returning `None`.
- The validation error text is verifiably included in the retry prompt (assertable via the mock's call args).

### T24 — Unit tests for structured output/retry (mocked LLM)
**Depends on:** T23
**Description:** Expand test coverage for T23 across edge cases: empty citations, wrong enum value, malformed JSON, and successful first-try path.
**Acceptance Criteria:**
- At least 4 distinct failure/success scenarios are covered by named test cases.
- All tests run without any real network/API calls (fully mocked).
- Test suite passes in CI.

---

## Phase 6 — Confidence & Refusal

### T25 — Confidence scoring module
**Depends on:** T18, T21
**Description:** Build `backend/app/rag/confidence.py` computing `retrieval_component` (normalized fused score of used citations) and `groundedness_component` (embedding similarity between answer text and cited excerpts), combined into a weighted `confidence_score`.
**Acceptance Criteria:**
- Given a high-similarity retrieval + high-overlap answer, the function returns a score close to 1.0.
- Given citations with low retrieval scores or an answer unrelated to its citations, the function returns a low score.
- Weights (`w1`, `w2`) are configurable via settings.

### T26 — Refusal/fallback decision logic + canned templates
**Depends on:** T25
**Description:** Build `backend/app/rag/refusal.py` implementing the pre-generation short-circuit (best fused score below threshold → skip LLM call) and post-generation override (low computed confidence → replace answer with a refusal template), per PLAN.md §7.
**Acceptance Criteria:**
- Given a query with no retrieved chunks above threshold, the function signals refusal before any LLM call is made (verifiable via a mock LLM call-count assertion).
- Given a generated answer whose computed confidence is below the post-generation threshold, the final response is overridden with the refusal template while retained low-confidence sources are still attached for transparency.
- Refusal template text explicitly recommends consulting a licensed lawyer.

---

## Phase 7 — RAG Orchestration

### T27 — Prompt templates per user_type + disclaimer injection
**Depends on:** T21
**Description:** Build `backend/app/rag/prompts.py` with system/human prompt templates for `layperson`, `law_student`, and `lawyer`, each embedding the legal disclaimer instruction.
**Acceptance Criteria:**
- Each of the 3 `user_type` values maps to a distinct prompt template.
- Every template's rendered system prompt contains the disclaimer instruction text.
- Unit test renders each template with sample context and confirms required placeholders (query, retrieved context) are substituted correctly.

### T28 — SQLite session/message store + CRUD
**Depends on:** T03
**Description:** Build `backend/app/services/session_store.py` with SQLite-backed `sessions` and `messages` tables and functions to create a session, append a message, and fetch history by `session_id`.
**Acceptance Criteria:**
- Creating a session and appending 3 messages, then fetching history, returns them in correct chronological order.
- Fetching history for a nonexistent `session_id` returns an empty list, not an error.
- Data persists across process restarts (backed by a file-based SQLite DB, not in-memory).

### T29 — Condense-question step for multi-turn follow-ups
**Depends on:** T22, T28
**Description:** Build `backend/app/rag/condense.py` that uses the LLM to rewrite a follow-up question into a standalone query given prior session history.
**Acceptance Criteria:**
- Given a history like "What is the penalty for theft?" followed by "What if it's a repeat offense?", the condensed output is a standalone question mentioning theft/repeat offense (verified via mocked LLM returning a fixed rewrite, and a real-call smoke test).
- If there is no prior history, the function returns the original query unchanged without an LLM call.
- Function is async and awaitable.

### T30 — Assemble full LCEL RAG chain end-to-end
**Depends on:** T19, T23, T26, T27, T29
**Description:** Build `backend/app/rag/chain.py` wiring: condense question → hybrid retrieve (+ optional rerank) → pre-generation refusal check → prompt construction → structured LLM call w/ retry → confidence scoring → post-generation refusal check → final `LegalAnswerResponse` assembly.
**Acceptance Criteria:**
- Given a fixture corpus and a mocked LLM, invoking the chain with a well-covered query returns a `LegalAnswerResponse` with non-empty citations and `is_refusal=False`.
- Given a query with no relevant fixture content, the chain returns a refusal response without ever calling the mocked LLM's generation method.
- The chain is invocable both sync and async.

### T31 — End-to-end RAG chain test (fixture corpus + mocked LLM)
**Depends on:** T30
**Description:** Write a comprehensive integration test suite exercising T30 across multiple domains, multi-turn conversations, and both `user_type` and refusal paths.
**Acceptance Criteria:**
- At least one test per: single-turn success, multi-turn follow-up, low-confidence refusal, no-context refusal.
- Test confirms citations in the response map back to fixture chunk metadata exactly.
- Full suite runs without any real network calls.

---

## Phase 8 — Caching

### T32 — Caching module (Redis response cache + semantic near-duplicate check)
**Depends on:** T03, T14
**Description:** Build `backend/app/rag/cache.py` with a Redis-backed exact-match response cache (`hash(normalized_query + user_type)`, TTL) and a semantic near-duplicate check against recently cached query embeddings (cosine > 0.95).
**Acceptance Criteria:**
- Storing then fetching a response for the same normalized query returns the cached object without hitting the backing store logic again.
- A paraphrased near-duplicate query (cosine similarity above threshold in a test with fixed embeddings) hits the semantic cache.
- Cache functions degrade gracefully (log a warning, skip caching) if Redis is unreachable, rather than crashing the request.

### T33 — Wire caching into chat service
**Depends on:** T30, T32
**Description:** Build `backend/app/services/chat_service.py` that checks the cache before invoking the T30 chain and stores the result afterward.
**Acceptance Criteria:**
- Given a repeated identical query, the second call returns the cached result and does not re-invoke the RAG chain (verifiable via call-count assertion on a mocked chain).
- Cache is bypassed correctly when `consent_to_log`/caching is disabled by config for a request (if such an override exists) — otherwise documented as always-on.
- Service function is the single entrypoint used by the API layer (no direct chain calls elsewhere).

---

## Phase 9 — Backend API

### T34 — Bearer-token auth dependency
**Depends on:** T03
**Description:** Build `backend/app/core/security.py` with a FastAPI dependency validating `Authorization: Bearer <token>` against an env-configured token→tier mapping.
**Acceptance Criteria:**
- Request with a valid token passes through; request with missing/invalid token returns 401.
- Token-to-tier mapping is loaded from settings, not hardcoded in the dependency function.
- Unit test covers valid, missing, and malformed header cases.

### T35 — Rate limiting middleware (per token, Redis-backed)
**Depends on:** T32, T34
**Description:** Integrate `slowapi` (or equivalent) keyed by the authenticated token/tier, backed by Redis, configurable requests-per-minute per tier.
**Acceptance Criteria:**
- Exceeding the configured request rate for a token returns HTTP 429 with a clear error body.
- Different tokens have independent rate-limit counters.
- Rate limit resets after the configured window (verified with a short test window).

### T36 — Consent-aware query logging service
**Depends on:** T28
**Description:** Build `backend/app/services/query_log.py` writing to a SQLite `query_logs` table: timestamp, hashed token id, query (full text only if `consent_to_log=true`, else hash-only), retrieved chunk ids, confidence score, latency, model used.
**Acceptance Criteria:**
- A logged entry with `consent_to_log=true` stores the raw query text; with `false`, only a hash is stored and the raw text field is empty/null.
- Every field in the schema is populated for a sample logged request.
- Logging failures (e.g. DB write error) are caught and do not fail the parent request.

### T37 — POST /api/v1/chat endpoint (full wiring)
**Depends on:** T33, T34, T35, T36
**Description:** Build the main chat endpoint in `backend/app/api/routes/chat.py`: validates auth, applies rate limiting, calls `chat_service`, logs the query, and returns `LegalAnswerResponse`.
**Acceptance Criteria:**
- A valid authenticated request with a well-covered query returns HTTP 200 with a body matching `LegalAnswerResponse`'s schema.
- An unauthenticated request returns 401 before any chain/LLM logic executes.
- Endpoint is fully async and awaits the chat service without blocking the event loop (verified via a concurrency smoke test — multiple simultaneous requests complete without serialized blocking).

### T38 — GET /api/v1/sessions/{id}/history endpoint
**Depends on:** T28, T34
**Description:** Build the history-retrieval endpoint returning the ordered message list for a given `session_id`, behind bearer auth.
**Acceptance Criteria:**
- Returns the correct ordered history for an existing session.
- Returns an empty list (200), not an error, for an unknown session id.
- Requires valid auth like all other endpoints.

### T39 — GET /api/v1/domains and GET /api/v1/health endpoints
**Depends on:** T21, T34
**Description:** Build two lightweight endpoints: `/domains` (lists the 6 supported `LegalDomain` values) and `/health` (liveness check, no auth required).
**Acceptance Criteria:**
- `/domains` returns exactly the 6 configured domains (excluding `other`) with human-readable labels.
- `/health` returns 200 without requiring a bearer token.
- Both endpoints respond in under a few milliseconds (no heavy dependencies on the request path).

### T40 — FastAPI integration test suite
**Depends on:** T37, T38, T39
**Description:** Write end-to-end API tests using `TestClient`/`httpx.AsyncClient` covering auth failure, rate-limit trip, happy-path chat, refusal-path chat, and history retrieval, with the RAG chain mocked.
**Acceptance Criteria:**
- Test suite covers at least 6 distinct scenarios (401, 429, 200 happy path, refusal response shape, history round-trip, health check).
- No test depends on a real Gemini API key or real Redis instance (mocked/fakeredis).
- Suite runs in CI in under ~30 seconds.

---

## Phase 10 — Frontend

### T41 — Scaffold Next.js 15 app router + Tailwind
**Depends on:** T01
**Description:** Initialize the `frontend/` Next.js 15 project (App Router) with TypeScript and Tailwind CSS configured.
**Acceptance Criteria:**
- `npm run dev` serves a default page at `localhost:3000` with Tailwind styles visibly applied.
- TypeScript strict mode is enabled with no compile errors on the scaffold.
- Basic folder structure (`app/`, `components/`, `lib/`) is in place.

### T42 — Next.js API proxy route /api/chat
**Depends on:** T41
**Description:** Build `frontend/app/api/chat/route.ts` that forwards the client's chat request to the FastAPI backend, attaching the bearer token from server-side env vars.
**Acceptance Criteria:**
- The route never reads the backend token from any client-supplied value — it comes only from `process.env` on the server.
- A request to `/api/chat` with a valid backend running returns the backend's JSON response unmodified (aside from stripping any sensitive headers).
- The backend token is verifiably absent from the response sent to the browser (inspect response headers/body in a test).

### T43 — Chat UI shell (message list + input, local state)
**Depends on:** T41
**Description:** Build the core chat page (`app/page.tsx`) with a scrollable message list and a text input/send button, using local component state for now (no backend wiring yet).
**Acceptance Criteria:**
- Typing a message and clicking "Send" appends it to the visible message list.
- Input clears after sending; empty messages cannot be sent.
- UI is responsive and usable on both desktop and mobile viewport widths.

### T44 — Answer detail components (CitationCard + ConfidenceBadge)
**Depends on:** T41
**Description:** Build reusable components rendering a single citation (document, section, excerpt, relevance score) and a color-coded confidence badge (green/yellow/red by threshold).
**Acceptance Criteria:**
- `CitationCard` renders all 4 fields legibly given sample citation data.
- `ConfidenceBadge` renders green for scores above the high threshold, yellow for mid-range, red for low, using the same thresholds as the backend's refusal logic.
- Both components have basic snapshot/unit tests.

### T45 — DisclaimerBanner + consent checkbox
**Depends on:** T41
**Description:** Build a persistent disclaimer banner ("not a substitute for licensed legal counsel") and a consent checkbox controlling the `consent_to_log` flag sent with requests.
**Acceptance Criteria:**
- Banner is visible on the chat page at all times without requiring scrolling to find it.
- Consent checkbox defaults to a documented value (on or off) and its state is readable by the parent chat component.
- Unchecking consent is reflected in subsequent outgoing request payloads once wired (verified once T46/T47 land, or via a stub handler now).

### T46 — user_type selector wired into request payload
**Depends on:** T43
**Description:** Add a `layperson`/`law_student`/`lawyer` selector to the chat UI, defaulting to `layperson`, whose value is included in the outgoing chat request payload.
**Acceptance Criteria:**
- Selector changes are reflected in component state immediately.
- The constructed request payload (inspectable via a test or dev-tools network call) includes the currently selected `user_type`.
- Default value on first load is `layperson`.

### T47 — Session persistence + full backend wiring
**Depends on:** T42, T43, T44, T45, T46
**Description:** Wire the chat UI to call the T42 proxy route on send, persist a `session_id` in `localStorage`, display returned citations/confidence/disclaimer using T44/T45 components, and load prior history on page mount via the sessions endpoint.
**Acceptance Criteria:**
- Sending a message triggers a real (or locally-run) backend round trip and renders the answer with citations and a confidence badge.
- Reloading the page restores the same session's prior messages from the backend.
- Network/backend errors are surfaced to the user as a visible error state, not a silent failure.

---

## Phase 11 — Evaluation

### T48 — Author 30-50 Q&A evaluation dataset
**Depends on:** T13
**Description:** Hand-write `backend/eval/qa_dataset.jsonl` with 30-50 question/answer pairs spanning all 6 domains, each including expected domain and expected section references.
**Acceptance Criteria:**
- File contains between 30 and 50 entries, with every domain represented at least 4 times.
- Every entry has `question`, `expected_domain`, and `expected_sections` (non-empty list) fields.
- Expected section references are verified by hand against the actual curated corpus (T05-T10).

### T49 — run_eval.py retrieval precision/recall scoring
**Depends on:** T17, T48
**Description:** Build `backend/eval/run_eval.py` that runs each eval question through the retrieval layer (T17's built indices) and computes precision@k/recall@k against `expected_sections`.
**Acceptance Criteria:**
- Running the script against the current corpus and eval set prints per-question and aggregate precision@k/recall@k.
- Script output is saved to a report file (e.g. `eval/results/retrieval_report.json`).
- Script runs without requiring any LLM API calls (retrieval-only mode).

### T50 — run_eval.py answer-correctness scoring + summary report
**Depends on:** T30, T49
**Description:** Extend `run_eval.py` to additionally run each question through the full RAG chain and score answer correctness (e.g. citation overlap with `expected_sections` plus a simple rubric/LLM-judge check), producing a combined markdown/CSV summary report.
**Acceptance Criteria:**
- Extended script produces a single report combining retrieval metrics and answer-correctness metrics per domain.
- Report clearly flags any eval questions that triggered an unexpected refusal or an unexpectedly confident wrong answer.
- Script is runnable as a standalone CLI command documented in the README.

---

## Phase 12 — Deployment

### T51 — Backend Dockerfile
**Depends on:** T02, T17
**Description:** Write `backend/Dockerfile` building the FastAPI service image, including a volume mount point for the FAISS index directory.
**Acceptance Criteria:**
- `docker build` succeeds and the resulting image starts the API and responds to `/health`.
- Image size and layer caching are reasonable (dependency install layer cached separately from app code).
- Container reads config from environment variables, not baked-in secrets.

### T52 — Frontend Dockerfile
**Depends on:** T41
**Description:** Write `frontend/Dockerfile` building a Next.js standalone production image.
**Acceptance Criteria:**
- `docker build` succeeds and the resulting container serves the app on the configured port.
- Production build does not include dev-only dependencies in the final image layer.
- Backend API URL is configurable via a runtime env var, not hardcoded at build time.

### T53 — docker-compose.yml (backend + frontend + redis + volumes)
**Depends on:** T51, T52
**Description:** Write root `docker-compose.yml` wiring the backend, frontend, and Redis services together with the FAISS index volume and shared `.env` configuration.
**Acceptance Criteria:**
- `docker compose up` brings up all 3 services and the frontend can successfully complete a chat round trip through the backend.
- Redis data and the FAISS index persist across a `docker compose down && docker compose up` cycle (named volumes).
- `.env.example` documents every environment variable required by the compose file.

### T54 — README + setup docs
**Depends on:** T17, T47, T53
**Description:** Write the final root `README.md` covering: project overview, architecture summary/diagram reference, local dev setup (backend + frontend without Docker), Docker Compose usage, ingestion/index-build steps, and how to run the evaluation script.
**Acceptance Criteria:**
- A new developer following the README from a clean checkout can get the full system running end-to-end (ingest → build index → docker compose up → send a chat message) without needing to ask questions.
- README links to `PRD.md` and `PLAN.md` for deeper context.
- README documents all required environment variables and where to obtain the Gemini API key.
