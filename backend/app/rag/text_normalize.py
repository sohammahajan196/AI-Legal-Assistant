"""Normalize LLM text fields that may contain literal escape sequences."""

from __future__ import annotations


def normalize_llm_text(text: str) -> str:
    """Convert literal ``\\n`` / ``\\t`` sequences from structured JSON output."""
    if "\\" not in text:
        return text
    return text.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
