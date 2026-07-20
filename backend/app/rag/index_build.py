"""
Offline index build: validate processed corpus, then build FAISS + BM25 indices.

See PLAN.md Section 3 and TASKS.md T17.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.logging import logger
from app.rag.bm25_index import build_bm25_index
from app.rag.corpus_validation import (
    CorpusValidationReport,
    format_validation_report,
    validate_corpus,
)
from app.rag.embeddings import get_embedding_model
from app.rag.ingestion import load_processed_chunks
from app.rag.vectorstore import build_faiss_index


class IndexBuildError(Exception):
    """Raised when corpus validation fails before any index artifacts are built."""


@dataclass(frozen=True)
class IndexBuildResult:
    """Summary of a successful FAISS + BM25 index build."""

    chunk_count: int
    faiss_index_dir: Path
    bm25_index_dir: Path
    validation_report: CorpusValidationReport


def build_all_indices(
    processed_root: Path,
    faiss_index_dir: Path,
    bm25_index_dir: Path,
    *,
    embedding_model: Any | None = None,
) -> IndexBuildResult:
    """Validate the processed corpus, then build and persist both retrieval indices."""
    logger.info("Document indexing started")
    try:
        report = validate_corpus(processed_root)
        if not report.ok:
            raise IndexBuildError(format_validation_report(report))

        chunks = load_processed_chunks(processed_root)
        if not chunks:
            raise ValueError(f"No chunks found under {processed_root}")

        model = embedding_model or get_embedding_model()
        build_faiss_index(chunks, model, str(faiss_index_dir))
        build_bm25_index(chunks, str(bm25_index_dir))
    except Exception as exc:
        logger.exception("Document indexing failed: %s", type(exc).__name__)
        raise

    logger.info("Document indexing completed")
    return IndexBuildResult(
        chunk_count=len(chunks),
        faiss_index_dir=faiss_index_dir,
        bm25_index_dir=bm25_index_dir,
        validation_report=report,
    )
