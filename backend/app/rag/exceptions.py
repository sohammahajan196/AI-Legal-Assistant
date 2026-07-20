"""Domain errors raised by the retrieval stack."""

from __future__ import annotations

INDEX_BUILD_HINT = (
    "Run `python scripts/ingest.py` then `python scripts/build_index.py` "
    "from the backend directory."
)


class RetrievalIndexNotFoundError(FileNotFoundError):
    """FAISS or BM25 index artifacts are missing on disk."""

    def __init__(self, which: str, path: str, expected: str) -> None:
        self.which = which
        self.path = path
        detail = (
            f"{which} index not found at {path!r} (expected {expected}). "
            f"{INDEX_BUILD_HINT}"
        )
        super().__init__(detail)
