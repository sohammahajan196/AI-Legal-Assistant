"""
BM25 keyword index: build/persist/query.

See PLAN.md Section 4 and TASKS.md T16.
"""

from app.rag.chunking import LegalChunk


def build_bm25_index(chunks: list[LegalChunk]):
    """Build a BM25Retriever from processed chunks.

    TODO: implement using `langchain_community.retrievers.BM25Retriever`.
    """
    raise NotImplementedError


def query_bm25_index(index, query: str, k: int = 20):
    """Query the BM25 index for exact keyword/section-number matches.

    TODO: implement.
    """
    raise NotImplementedError
