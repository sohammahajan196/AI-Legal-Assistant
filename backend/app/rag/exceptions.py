"""Domain errors raised by the retrieval stack and RAG pipeline."""

from __future__ import annotations

__all__ = [
    "GeminiServiceUnavailableError",
    "INDEX_BUILD_HINT",
    "RetrievalIndexNotFoundError",
]

INDEX_BUILD_HINT = (
    "Run `python scripts/ingest.py` then `python scripts/build_index.py` "
    "from the backend directory."
)


class GeminiServiceUnavailableError(Exception):
    """Raised when Gemini is still unavailable after retries (and optional fallback).

    Mapped to HTTP 503 by the FastAPI exception handler in ``app.main``.
    """

    USER_MESSAGE = "Our AI service is temporarily busy. Please try again in a moment."

    def __init__(
        self,
        message: str = USER_MESSAGE,
        *,
        last_error: Exception | None = None,
        model: str | None = None,
        attempts: int = 0,
    ) -> None:
        super().__init__(message)
        self.last_error = last_error
        self.model = model
        self.attempts = attempts


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
