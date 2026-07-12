"""
Full LCEL RAG chain: condense question -> hybrid retrieve (+ optional rerank)
-> pre-generation refusal check -> prompt construction -> structured LLM call
-> confidence scoring -> post-generation refusal check -> final response
assembly.

See PLAN.md Section 5 and TASKS.md T30.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever

from app.core.config import settings
from app.rag.bm25_index import load_bm25_index
from app.rag.condense import condense_question
from app.rag.confidence import (
    compute_confidence_score,
    compute_groundedness_component,
    compute_retrieval_component,
)
from app.rag.embeddings import get_embedding_model
from app.rag.hybrid_retriever import HybridQueryResult, query_hybrid_index
from app.rag.llm import get_llm
from app.rag.prompts import RESPONSE_DISCLAIMER, build_prompt
from app.rag.reranker import build_reranking_retriever
from app.rag.refusal import (
    build_refusal_response,
    should_refuse_after_generation,
    should_refuse_before_generation,
)
from app.rag.structured_llm import StructuredOutputGenerationError, generate_structured_answer
from app.rag.vectorstore import load_faiss_index
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain, LLMStructuredAnswer, SourceCitation


@lru_cache(maxsize=1)
def _load_default_faiss_index():
    """Lazily load the production FAISS index (only hit when a test/caller
    doesn't inject a `faiss_index` override)."""
    return load_faiss_index(settings.faiss_index_dir, get_embedding_model())


@lru_cache(maxsize=1)
def _load_default_bm25_index():
    """Lazily load the production BM25 index (only hit when a test/caller
    doesn't inject a `bm25_index` override)."""
    return load_bm25_index(settings.bm25_index_dir)


def reset_default_index_cache() -> None:
    """Clear the cached production FAISS/BM25 index singletons (for tests)."""
    _load_default_faiss_index.cache_clear()
    _load_default_bm25_index.cache_clear()


class _FixedDocumentRetriever(BaseRetriever):
    """Wraps a precomputed document list as a `BaseRetriever` so the T19
    reranker (built against LangChain retriever chains) can be reused here
    without re-querying FAISS/BM25 a second time."""

    documents: list[Document] = []

    def _get_relevant_documents(self, query: str, *, run_manager: Any) -> list[Document]:
        return list(self.documents)


def _rerank_hybrid_results(results: list[HybridQueryResult], query: str) -> list[HybridQueryResult]:
    """Apply the optional cross-encoder reranker (T19) to fused hybrid results.

    Reordering/top-N selection only; each result's original fused-retrieval
    `score` is preserved (never replaced by the cross-encoder's own score) so
    citations/confidence scoring keep the normalized hybrid-retrieval score
    they're defined against. A no-op (returns `results` unchanged) when
    `settings.enable_reranker` is False, per T19's passthrough contract.
    """
    if not results:
        return results

    documents = [
        Document(page_content=result.text, metadata={"source_citation": result.source_citation})
        for result in results
    ]
    retriever = build_reranking_retriever(_FixedDocumentRetriever(documents=documents))
    reranked_documents = retriever.invoke(query)

    by_citation = {result.source_citation: result for result in results}
    return [by_citation[doc.metadata["source_citation"]] for doc in reranked_documents]


def _format_context(results: list[HybridQueryResult]) -> str:
    """Render retrieved chunks into the context block substituted into the
    prompt, each tagged with its citation id so the LLM can reference it in
    `used_citation_ids`."""
    if not results:
        return "No relevant source material was retrieved."

    blocks = []
    for result in results:
        title_suffix = f" - {result.section_title}" if result.section_title else ""
        blocks.append(
            f"[{result.source_citation}] {result.act_name} ({result.act_year}), "
            f"Section {result.section_number}{title_suffix}:\n{result.text}"
        )
    return "\n\n".join(blocks)


def _to_source_citation(result: HybridQueryResult) -> SourceCitation:
    return SourceCitation(
        document=result.act_name,
        act_year=result.act_year,
        section=result.section_number,
        domain=LegalDomain(result.domain),
        excerpt=result.text,
        retrieval_score=result.score,
    )


def _resolve_citations(used_citation_ids: list[str], results: list[HybridQueryResult]) -> list[SourceCitation]:
    """Map the LLM's `used_citation_ids` back to real retrieved chunks.

    Any id the LLM names that doesn't match an actually-retrieved chunk is
    silently dropped rather than surfaced -- citations are assembled
    server-side from real retrieval hits only; a `SourceCitation` is never
    fabricated from an LLM-invented id (see general.mdc).
    """
    by_citation = {result.source_citation: result for result in results}
    return [_to_source_citation(by_citation[cid]) for cid in used_citation_ids if cid in by_citation]


async def run_rag_chain(
    query: str,
    session_id: str | None,
    user_type: str,
    history: list[dict] | None = None,
    *,
    llm: Any = None,
    faiss_index: Any = None,
    bm25_index: Any = None,
    embedding_model: Embeddings | None = None,
) -> LegalAnswerResponse:
    """Execute the full RAG pipeline for a single user query.

    `session_id` is accepted for API-contract symmetry with `ChatRequest` /
    future logging use, but multi-turn history must be fetched by the caller
    (see `app.services.session_store`, T28) and passed in via `history` --
    this module has no direct T28 dependency (see TASKS.md T30's dependency
    list: T19/T23/T26/T27/T29, not T28).

    `llm`/`faiss_index`/`bm25_index`/`embedding_model` are override hooks for
    tests (fixture corpus, mocked LLM, deterministic embeddings); production
    callers should omit them and rely on the config-driven defaults.
    """
    resolved_llm = llm or get_llm()
    resolved_history = history or []

    standalone_query = await condense_question(resolved_llm, query, resolved_history)

    resolved_faiss = faiss_index if faiss_index is not None else _load_default_faiss_index()
    resolved_bm25 = bm25_index if bm25_index is not None else _load_default_bm25_index()

    results = await asyncio.to_thread(
        query_hybrid_index,
        resolved_faiss,
        resolved_bm25,
        standalone_query,
        k=settings.retrieval_top_k,
    )

    best_retrieval_score = max((result.score for result in results), default=0.0)
    if should_refuse_before_generation(best_retrieval_score):
        return build_refusal_response(LegalDomain.OTHER, RESPONSE_DISCLAIMER)

    reranked_results = await asyncio.to_thread(_rerank_hybrid_results, results, standalone_query)

    prompt_messages = build_prompt(user_type, query=standalone_query, context=_format_context(reranked_results))

    try:
        structured_answer = await generate_structured_answer(resolved_llm, prompt_messages, LLMStructuredAnswer)
    except StructuredOutputGenerationError:
        # Refuse rather than guess (general.mdc) -- a repair loop that never
        # converges is treated the same as "nothing trustworthy to answer with".
        return build_refusal_response(LegalDomain.OTHER, RESPONSE_DISCLAIMER)

    used_citations = _resolve_citations(structured_answer.used_citation_ids, reranked_results)

    retrieval_component = compute_retrieval_component(used_citations)
    groundedness_component = compute_groundedness_component(
        structured_answer.answer, used_citations, embedding_model=embedding_model
    )
    confidence_score = compute_confidence_score(retrieval_component, groundedness_component)

    if structured_answer.is_refusal or should_refuse_after_generation(confidence_score):
        return build_refusal_response(
            structured_answer.legal_domain,
            RESPONSE_DISCLAIMER,
            citations=used_citations,
            confidence_score=confidence_score,
        )

    return LegalAnswerResponse(
        answer=structured_answer.answer,
        confidence_score=confidence_score,
        legal_domain=structured_answer.legal_domain,
        citations=used_citations,
        is_refusal=False,
        disclaimer=RESPONSE_DISCLAIMER,
    )


def run_rag_chain_sync(
    query: str,
    session_id: str | None,
    user_type: str,
    history: list[dict] | None = None,
    *,
    llm: Any = None,
    faiss_index: Any = None,
    bm25_index: Any = None,
    embedding_model: Embeddings | None = None,
) -> LegalAnswerResponse:
    """Synchronous entrypoint wrapping `run_rag_chain` (TASKS.md T30: "the
    chain is invocable both sync and async"). Async callers should await
    `run_rag_chain` directly rather than route through this wrapper."""
    return asyncio.run(
        run_rag_chain(
            query,
            session_id,
            user_type,
            history,
            llm=llm,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
            embedding_model=embedding_model,
        )
    )
