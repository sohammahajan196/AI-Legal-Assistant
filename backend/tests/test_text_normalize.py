"""Tests for app.rag.text_normalize."""

from app.rag.text_normalize import normalize_llm_text


def test_normalize_llm_text_passes_through_plain_text():
    assert normalize_llm_text("Plain answer.") == "Plain answer."


def test_normalize_llm_text_converts_literal_escape_sequences():
    assert normalize_llm_text("Line one\\n\\nLine two") == "Line one\n\nLine two"
