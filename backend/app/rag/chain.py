"""
Full LCEL RAG chain: condense question -> hybrid retrieve (+ optional rerank)
-> pre-generation refusal check -> prompt construction -> structured LLM call
-> confidence scoring -> post-generation refusal check -> final response
assembly.

See PLAN.md Section 5 and TASKS.md T30.
"""

from app.schemas.legal_answer import LegalAnswerResponse


async def run_rag_chain(query: str, session_id: str | None, user_type: str) -> LegalAnswerResponse:
    """Execute the full RAG pipeline for a single user query.

    TODO: wire together app.rag.condense, app.rag.hybrid_retriever,
    app.rag.reranker, app.rag.refusal, app.rag.prompts,
    app.rag.structured_llm, and app.rag.confidence, per PLAN.md Section 5.
    """
    raise NotImplementedError
