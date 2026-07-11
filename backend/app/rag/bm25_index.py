"""
BM25 keyword index: build/persist/query.

See PLAN.md Section 4 and TASKS.md T16.
"""

from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from app.rag.chunking import LegalChunk
from app.rag.vectorstore import chunk_to_document

BM25_INDEX_FILE = "bm25_retriever.pkl"
DEFAULT_BM25_TOP_K = 20
_LEGAL_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def legal_bm25_preprocess(text: str) -> list[str]:
    """Tokenize legal text for BM25, preserving section ids like ``304A``."""
    return _LEGAL_TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Bm25QueryResult:
    """A single BM25 retrieval hit with citation metadata and rank-based score."""

    text: str
    score: float
    domain: str
    act_name: str
    act_year: int
    chapter: str | None
    section_number: str
    section_title: str | None
    source_citation: str

    @classmethod
    def from_document(cls, doc: Document, rank: int) -> Bm25QueryResult:
        metadata = doc.metadata
        # BM25Retriever returns ranked docs without raw scores; use reciprocal rank.
        score = 1.0 / (rank + 1)
        return cls(
            text=doc.page_content,
            score=score,
            domain=str(metadata["domain"]),
            act_name=str(metadata["act_name"]),
            act_year=int(metadata["act_year"]),
            chapter=_metadata_optional_str(metadata.get("chapter")),
            section_number=str(metadata["section_number"]),
            section_title=_metadata_optional_str(metadata.get("section_title")),
            source_citation=str(metadata["source_citation"]),
        )


def _metadata_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_bm25_index(chunks: list[LegalChunk], persist_dir: str) -> None:
    """Build a BM25Retriever from processed chunks and persist it to disk."""
    if not chunks:
        raise ValueError("Cannot build a BM25 index from an empty chunk list")

    documents = [chunk_to_document(chunk) for chunk in chunks]
    retriever = BM25Retriever.from_documents(
        documents,
        preprocess_func=legal_bm25_preprocess,
    )
    retriever.k = DEFAULT_BM25_TOP_K

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)
    with open(persist_path / BM25_INDEX_FILE, "wb") as handle:
        pickle.dump(retriever, handle)


def load_bm25_index(persist_dir: str) -> BM25Retriever:
    """Load a previously persisted BM25 retriever from *persist_dir*."""
    persist_path = Path(persist_dir)
    index_path = persist_path / BM25_INDEX_FILE

    if not index_path.is_file():
        raise FileNotFoundError(
            f"BM25 index not found at {persist_dir!r} (expected {BM25_INDEX_FILE!r})"
        )

    with open(index_path, "rb") as handle:
        return pickle.load(handle)


def query_bm25_index(
    index: BM25Retriever,
    query: str,
    k: int = 20,
    domain: str | None = None,
) -> list[Bm25QueryResult]:
    """Query the BM25 index for exact keyword/section-number matches."""
    if k < 1:
        raise ValueError("k must be at least 1")

    original_k = index.k
    try:
        if domain is None:
            index.k = k
            documents = index.invoke(query)
        else:
            fetch_n = min(len(index.docs), max(k * 10, k))
            index.k = fetch_n
            documents = [
                doc
                for doc in index.invoke(query)
                if str(doc.metadata.get("domain")) == domain
            ][:k]

        return [
            Bm25QueryResult.from_document(doc, rank)
            for rank, doc in enumerate(documents)
        ]
    finally:
        index.k = original_k
