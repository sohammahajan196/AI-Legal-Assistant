"""
Hybrid retrieval: fuses FAISS (semantic) and BM25 (keyword) results via
Reciprocal Rank Fusion using LangChain's EnsembleRetriever.

See PLAN.md Section 4 and TASKS.md T18.
"""


def build_hybrid_retriever(faiss_retriever, bm25_retriever, weights: tuple[float, float] = (0.5, 0.5)):
    """Combine the two retrievers into a single `EnsembleRetriever`.

    TODO: implement using `langchain.retrievers.EnsembleRetriever`, with
    `weights` configurable rather than hardcoded.
    """
    raise NotImplementedError


def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalize a list of raw fused scores to the [0, 1] range.

    TODO: implement.
    """
    raise NotImplementedError
