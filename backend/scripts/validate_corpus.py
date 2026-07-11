"""
CLI: QA pass over processed chunks (data/processed/<domain>.jsonl).

Checks for empty text, duplicate section numbers within an act, and missing
metadata; prints a per-domain summary report.

See TASKS.md T13.

Usage (from backend/):
    python scripts/validate_corpus.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.corpus_validation import format_validation_report, validate_corpus  # noqa: E402

PROCESSED_ROOT = BACKEND_ROOT / "data" / "processed"


def main() -> int:
    """Validate processed JSONL corpora and print a per-domain summary."""
    report = validate_corpus(PROCESSED_ROOT)
    print(format_validation_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
