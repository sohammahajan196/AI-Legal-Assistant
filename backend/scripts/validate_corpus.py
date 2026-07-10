"""
CLI: QA pass over processed chunks (data/processed/<domain>.jsonl).

Checks for empty text, duplicate section numbers within an act, and missing
metadata; prints a per-domain summary report.

See TASKS.md T13.

Usage:
    python scripts/validate_corpus.py
"""


def main() -> None:
    """Entry point for the corpus validation CLI.

    TODO: implement the validation checks described above and exit
    non-zero if any check fails.
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
