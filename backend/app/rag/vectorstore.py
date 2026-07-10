"""
FAISS vector store: build/persist/query, domain-filterable.

See PLAN.md Section 3 and TASKS.md T15.
"""

from app.rag.chunking import LegalChunk


def build_faiss_index(chunks: list[LegalChunk], embedding_model, persist_dir: str) -> None:
    """Build a FAISS index from processed chunks and persist it to disk.

    TODO: implement using `langchain_community.vectorstores.FAISS`.
    """
    raise NotImplementedError


def load_faiss_index(persist_dir: str, embedding_model):
    """Load a previously persisted FAISS index.

    TODO: implement.
    """
    raise NotImplementedError


def query_faiss_index(index, query: str, k: int = 20, domain: str | None = None):
    """Query the FAISS index, optionally filtered by legal domain metadata.

    TODO: implement metadata filter support so domain-scoped queries exclude
    chunks from other domains.
    """
    raise NotImplementedError
