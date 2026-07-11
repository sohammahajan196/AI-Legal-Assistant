"""
CLI: runs corpus validation, then builds both the FAISS and BM25 index
artifacts in one command.

See PLAN.md Section 3 and TASKS.md T17.

Usage (from backend/):
    python scripts/build_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.rag.corpus_validation import format_validation_report  # noqa: E402
from app.rag.bm25_index import BM25_INDEX_FILE  # noqa: E402
from app.rag.index_build import IndexBuildError, build_all_indices  # noqa: E402
from app.rag.vectorstore import FAISS_DOCSTORE_FILE, FAISS_INDEX_FILE  # noqa: E402

PROCESSED_ROOT = BACKEND_ROOT / "data" / "processed"


def main() -> int:
    """Validate processed JSONL corpora, then build FAISS and BM25 indices."""
    faiss_index_dir = Path(settings.faiss_index_dir)
    bm25_index_dir = Path(settings.bm25_index_dir)

    try:
        result = build_all_indices(
            PROCESSED_ROOT,
            faiss_index_dir,
            bm25_index_dir,
        )
    except IndexBuildError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        return 1

    print(format_validation_report(result.validation_report))
    print("")
    print(f"FAISS index -> {result.faiss_index_dir} ({FAISS_INDEX_FILE}, {FAISS_DOCSTORE_FILE})")
    print(f"BM25 index -> {result.bm25_index_dir} ({BM25_INDEX_FILE})")
    print(f"Done. Indexed {result.chunk_count} chunks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
