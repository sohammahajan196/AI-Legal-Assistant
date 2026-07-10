"""
CLI: raw act text (data/raw/<domain>/*.txt) -> processed, chunked,
metadata-tagged JSONL (data/processed/<domain>.jsonl).

See PLAN.md Section 3 and TASKS.md T12.

Usage:
    python scripts/ingest.py
"""


def main() -> None:
    """Entry point for the ingestion CLI.

    TODO: walk `data/raw/<domain>/*.txt`, run
    `app.rag.chunking.parse_act_text` on each file, and write one JSONL file
    per domain to `data/processed/`. Must be idempotent (T12).
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
