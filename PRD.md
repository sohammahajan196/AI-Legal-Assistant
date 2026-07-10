# Product Requirements Document: AI Legal Assistant for Indian Law

**Status:** Draft
**Version:** 1.0
**Scope:** MVP (functional end-to-end demo, simplified auth/deployment)
**Related doc:** [PLAN.md](./PLAN.md) — technical architecture derived from this PRD

---

## 1. Summary

An AI-powered legal assistant that answers questions about Indian law through a Retrieval-Augmented Generation (RAG) pipeline. Every answer is grounded in retrieved statutory text, cites its exact source (act + section), and carries a computed confidence score — instead of a free-form LLM response that can hallucinate legal provisions. The product's core value proposition is **trust through traceability**, not raw answer fluency.

## 2. Problem Statement

Indian legal information is fragmented across many domains (criminal, civil, family, labour, consumer, property, etc.) and written in dense statutory language that is hard for non-lawyers to interpret. Generic LLM chatbots:

- Hallucinate section numbers, penalties, and procedures.
- Give no way for a user to verify the claim against an actual source.
- Use one-size-fits-all explanations regardless of the user's legal literacy.

This product addresses these failure modes by (a) constraining generation to retrieved source text, (b) surfacing citations and a confidence score with every answer, and (c) adapting explanation style to the user's background.

## 3. Goals

### 3.1 Product goals

- Answer natural-language legal questions with citation-backed, verifiable responses.
- Make every claim traceable to a specific act/section, so a user (or reviewer) can check the primary source.
- Communicate uncertainty honestly — refuse or hedge when retrieval confidence is low, rather than guessing.
- Adapt explanation depth/tone to the asker (layperson vs. law student vs. legal professional).
- Support natural follow-up conversation (multi-turn), not just single-shot Q&A.

### 3.2 Business/portfolio goals

- Demonstrate a production-grade RAG architecture (hybrid retrieval, structured output contracts, confidence scoring) as a portfolio-quality system.
- Keep infrastructure cost and operational complexity low enough for a solo-maintained MVP (SQLite/Redis/Docker, no managed cloud dependencies required).

### 3.3 Non-goals (explicit out of scope)

- Not a substitute for licensed legal counsel — must be surfaced in the UI and reinforced at the system-prompt level.
- Not intended to generate legal documents (contracts, petitions, notices) or provide binding legal advice.
- Not a case-law / judgment search engine in v1 (statutory bare acts only; case law is a future extension).
- No user account system / multi-tenant billing in v1 (static bearer tokens only).

## 4. Target Users & Personas

| Persona | Description | Needs from the product |
|---|---|---|
| Layperson | No legal training, e.g. a tenant, employee, or consumer with a dispute | Plain-language answers, minimal jargon, clear "what should I do" framing, strong disclaimers |
| Law student | Studying Indian law, wants to verify or study provisions | Precise section citations, more technical language, willingness to see nuance/exceptions |
| Legal professional | Practicing lawyer/paralegal doing a quick lookup | Fast, precise citation retrieval; minimal hand-holding; trusts citations over prose |

`user_type` is an explicit input to every query and drives prompt adaptation (see PLAN.md Section 5).

## 5. Use Cases / User Stories

1. As a layperson, I want to ask "What can I do if my landlord won't return my security deposit?" and get a plain-language answer citing the relevant Act/section, so I know my rights without hiring a lawyer just to find out.
2. As a law student, I want to ask "What is Section 304A IPC?" and get the precise statutory text with citation, so I can verify it against my coursework.
3. As any user, I want to ask a follow-up like "What if the employer is a government body?" after an initial labour-law question, and have the system understand it's still about the same topic.
4. As any user, I want to see exactly which document/section the system used, so I can independently verify the answer.
5. As any user, when the system isn't confident, I want it to say so explicitly and tell me to consult a lawyer, rather than confidently guessing.
6. As a product owner, I want a small evaluation set so I can measure whether retrieval/answer quality improves or regresses as the corpus and pipeline evolve.

## 6. Functional Requirements

### 6.1 Legal domain coverage (v1)

Six domains, each backed by at least one authoritative bare act (full list and source acts in [PLAN.md §1](./PLAN.md#1-legal-domain-list-final-6-domains--fallback)):

1. Criminal
2. Civil
3. Family
4. Labour
5. Consumer Protection
6. Property

Plus an `other` fallback classification for out-of-scope queries (triggers cautious/refusal behavior rather than a forced answer).

### 6.2 Data ingestion

- System must ingest bare acts as structured, section-level chunks (not fixed-size token windows), preserving section number, chapter, and act metadata for citation purposes.
- Ingestion is a repeatable offline process, not a live scraping dependency at request time.

### 6.3 Retrieval

- Every query must be answered using hybrid retrieval: semantic (embeddings) + keyword (exact term/section-number matching), fused via a principled method (Reciprocal Rank Fusion), not naive concatenation.
- Retrieval must support filtering/segmentation by legal domain.

### 6.4 Answer generation

- Answers must be generated only from retrieved source text (no unconstrained free generation).
- Output must always include: answer text, a numeric confidence score, one or more source citations (or none, if refusing), and a legal domain classification.
- The system must support multi-turn conversations where follow-up questions retain prior context.
- The system must adapt explanation tone/complexity based on declared `user_type`.

### 6.5 Trust & explainability

- Every citation shown to the user must be traceable to a real ingested document/section — never fabricated.
- The confidence score must be computed from retrieval/groundedness signals, not solely the LLM's self-reported confidence.
- When confidence is low or no relevant text is found, the system must return an explicit refusal/fallback message directing the user to consult a licensed lawyer, instead of answering anyway.

### 6.6 API & security

- All backend endpoints require bearer-token authentication.
- Requests must be rate-limited per token.
- The frontend must never expose the backend token to the browser (proxy pattern via Next.js API routes).

### 6.7 Frontend

- Chat-style interface for asking questions and viewing history within a session.
- Every answer must visibly display its citations and confidence score alongside the text.
- A legal disclaimer must be persistently visible in the UI.
- Users must be able to select their `user_type` and give explicit consent before their queries are logged.

### 6.8 Deployment

- The full system (backend, frontend, cache) must run via a single `docker-compose` command for local/demo deployment.

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | Cache repeated/near-identical queries (embedding- and/or full-response-level) to reduce latency and LLM cost |
| Privacy | Query logging must respect user consent; unconsented queries are logged only in hashed/anonymized form |
| Reliability | Structured LLM output must be validated against a schema; on validation failure, retry with the error fed back to the model rather than failing the user's request |
| Auditability | All served answers should be logged with enough metadata (retrieved sources, confidence, latency) to support later review |
| Evaluability | A hand-curated evaluation set (30-50 Q&A pairs across all domains) must exist to measure retrieval precision/recall and answer accuracy over time |
| Async/scalability | Embedding, retrieval, and LLM calls must be non-blocking so one slow request doesn't stall others |

## 8. Success Metrics

Since this is an MVP/portfolio system rather than a monetized product, success is measured technically rather than commercially:

- **Retrieval quality**: precision@k / recall@k against the evaluation set's expected section references (target: directionally improving as corpus/tuning matures; no hard SLA for v1).
- **Groundedness**: proportion of served (non-refused) answers whose citations genuinely support the answer text, spot-checked against the eval set.
- **Refusal calibration**: the system should refuse on genuinely out-of-corpus/ambiguous questions in the eval set, and should not refuse on well-covered ones — tracked as a false-refusal / false-confidence rate.
- **Latency**: end-to-end p95 response time for a cache-miss query (informal target, not a contractual SLA for MVP).
- **Cache effectiveness**: hit rate on repeated/near-duplicate queries.

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Legal/liability exposure from incorrect answers | Persistent disclaimer in UI + system prompt; explicit refusal path for low confidence; statutory-text-only grounding (no free legal advice generation) |
| Corpus staleness (laws amended/repealed, e.g. IPC/CrPC being superseded by BNS/BNSS) | Document corpus vintage clearly (act + year) in citations; design ingestion pipeline to be re-run when the corpus is refreshed |
| Data sourcing brittleness (India Code portal is JS-heavy, hard to scrape reliably) | Semi-manual curation workflow (documented download + convert + parse steps) rather than a fragile live scraper (see PLAN.md §1) |
| LLM structured-output failures | Native JSON-schema-constrained decoding + bounded retry-with-repair loop before failing the request |
| Over-confident wrong answers | Confidence computed server-side from retrieval/groundedness signals, not LLM self-report; low-confidence answers are overridden with a refusal template |
| Narrow v1 corpus (1-2 acts/domain) may not cover many real questions | Refusal fallback for out-of-corpus questions is a first-class behavior, not a bug; corpus is designed to be incrementally expandable |

## 10. Assumptions & Dependencies

- Google Gemini is the LLM provider (via `langchain-google-genai`), assumed available via API key.
- Legal source texts are sourced from public government portals (India Code) under fair-use/informational reproduction for a non-commercial demo; no proprietary/paid legal databases are used in v1.
- Single-instance deployment (Docker Compose) is sufficient; no multi-region or high-availability requirement for MVP.

## 11. Milestones (maps to PLAN.md implementation phases)

1. Data sourcing & section-aware ingestion pipeline (corpus + FAISS/BM25 index).
2. Backend RAG core (hybrid retrieval, RAG chain, structured output, confidence scoring, refusal logic).
3. FastAPI service layer (auth, rate limiting, sessions, caching, logging).
4. Next.js frontend (chat UI, citations/confidence display, disclaimers/consent).
5. Dockerization.
6. Evaluation set + scoring script.

## 12. Open Questions

- Should case law (judgments) be added as a source type in a future version, alongside bare acts?
- Should the corpus track the newer Bharatiya Nyaya Sanhita (BNS)/BNSS in addition to/instead of IPC/CrPC?
- Is a future multi-user account system (vs. static bearer tokens) in scope for a v2?
