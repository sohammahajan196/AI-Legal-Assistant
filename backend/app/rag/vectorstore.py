"""
FAISS vector store: build/persist/query, domain-filterable.

See PLAN.md Section 3 and TASKS.md T15.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.rag.chunking import LegalChunk

# Files written by ``FAISS.save_local`` (used by tests and manual checks).
FAISS_INDEX_FILE = "index.faiss"
FAISS_DOCSTORE_FILE = "index.pkl"


@dataclass(frozen=True)
class FaissQueryResult:
    """A single FAISS retrieval hit with citation metadata and similarity score."""

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
    def from_document(cls, doc: Document, score: float) -> FaissQueryResult:
        metadata = doc.metadata
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


def _chunk_metadata(chunk: LegalChunk) -> dict[str, str | int]:
    """Convert chunk fields to FAISS-safe metadata (no ``None`` values)."""
    return {
        "domain": chunk.domain,
        "act_name": chunk.act_name,
        "act_year": chunk.act_year,
        "chapter": chunk.chapter or "",
        "section_number": chunk.section_number,
        "section_title": chunk.section_title or "",
        "source_citation": chunk.source_citation,
    }


def _searchable_page_content(chunk: LegalChunk) -> str:
    """Build indexed text that includes section identifiers for keyword retrieval.

    Processed chunk bodies often omit the ``Section N.`` header (kept in
    metadata only). BM25 needs those tokens in ``page_content`` so queries
    like ``304A`` can match.
    """
    header_parts = [f"Section {chunk.section_number}."]
    if chunk.section_title:
        header_parts.append(chunk.section_title)
    header_parts.append(chunk.source_citation)
    header = " ".join(header_parts)
    body = chunk.text.strip()
    return f"{header}\n{body}" if body else header


def chunk_to_document(chunk: LegalChunk) -> Document:
    """Map a ``LegalChunk`` to a LangChain ``Document`` for indexing."""
    return Document(
        page_content=_searchable_page_content(chunk),
        metadata=_chunk_metadata(chunk),
    )


def build_faiss_index(chunks: list[LegalChunk], embedding_model, persist_dir: str) -> None:
    """Build a FAISS index from processed chunks and persist it to disk."""
    if not chunks:
        raise ValueError("Cannot build a FAISS index from an empty chunk list")

    documents = [chunk_to_document(chunk) for chunk in chunks]
    vectorstore = FAISS.from_documents(documents, embedding_model)

    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(persist_path))


def load_faiss_index(persist_dir: str, embedding_model):
    """Load a previously persisted FAISS index from *persist_dir*."""
    persist_path = Path(persist_dir)
    index_path = persist_path / FAISS_INDEX_FILE
    docstore_path = persist_path / FAISS_DOCSTORE_FILE

    if not index_path.is_file() or not docstore_path.is_file():
        raise FileNotFoundError(
            f"FAISS index not found at {persist_dir!r} "
            f"(expected {FAISS_INDEX_FILE!r} and {FAISS_DOCSTORE_FILE!r})"
        )

    return FAISS.load_local(
        str(persist_path),
        embedding_model,
        allow_dangerous_deserialization=True,
    )


def query_faiss_index(
    index,
    query: str,
    k: int = 20,
    domain: str | None = None,
) -> list[FaissQueryResult]:
    """Query the FAISS index, optionally filtered by legal domain metadata."""
    if k < 1:
        raise ValueError("k must be at least 1")

    search_kwargs: dict[str, Any] = {"k": k}
    if domain is not None:
        search_kwargs["filter"] = {"domain": domain}

    hits = index.similarity_search_with_score(query, **search_kwargs)
    return [FaissQueryResult.from_document(doc, score) for doc, score in hits]
