"""
CLI: raw act text (data/raw/<domain>/*.txt) -> processed, chunked,
metadata-tagged JSONL (data/processed/<domain>.jsonl).

See PLAN.md Section 3 and TASKS.md T12.

Usage (from backend/):
    python scripts/ingest.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.ingestion import ingest_all  # noqa: E402

RAW_ROOT = BACKEND_ROOT / "data" / "raw"
PROCESSED_ROOT = BACKEND_ROOT / "data" / "processed"


def main() -> int:
    """Walk raw domain folders, parse acts, and write processed JSONL files."""
    results = ingest_all(RAW_ROOT, PROCESSED_ROOT)

    for result in results:
        act_summary = ", ".join(
            f"{filename}={count}"
            for filename, count in sorted(result.act_chunk_counts.items())
        )
        print(
            f"{result.domain}: {result.chunk_count} chunks -> {result.output_path} "
            f"({act_summary})"
        )

    total_chunks = sum(result.chunk_count for result in results)
    print(f"Done. {len(results)} domain files, {total_chunks} total chunks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
