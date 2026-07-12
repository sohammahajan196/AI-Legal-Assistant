"""Unit tests for app.rag.refusal. See TASKS.md T26."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.rag.refusal import (
    REFUSAL_TEMPLATE,
    build_refusal_response,
    should_refuse_after_generation,
    should_refuse_before_generation,
)
from app.schemas.legal_answer import LegalDomain, SourceCitation

DISCLAIMER = (
    "This is not a substitute for licensed legal counsel. "
    "Consult a qualified lawyer for advice on your specific situation."
)


def _citation(retrieval_score: float, excerpt: str = "Whoever causes death by negligence...") -> SourceCitation:
    return SourceCitation(
        document="Indian Penal Code",
        act_year=1860,
        section="304A",
        domain=LegalDomain.CRIMINAL,
        excerpt=excerpt,
        retrieval_score=retrieval_score,
    )


# --- should_refuse_before_generation -----------------------------------------


def test_should_refuse_before_generation_true_when_score_below_threshold():
    assert should_refuse_before_generation(0.1, threshold=0.4) is True


def test_should_refuse_before_generation_false_when_score_above_threshold():
    assert should_refuse_before_generation(0.6, threshold=0.4) is False


def test_should_refuse_before_generation_boundary_score_equal_to_threshold_does_not_refuse():
    """A score exactly at the threshold clears the bar (strict `<` refusal)."""
    assert should_refuse_before_generation(0.4, threshold=0.4) is False


def test_should_refuse_before_generation_defaults_to_configured_threshold(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("CONFIDENCE_REFUSAL_THRESHOLD", "0.5")

    with patch("app.rag.refusal.settings", Settings(_env_file=None)):  # type: ignore[call-arg]
        assert should_refuse_before_generation(0.45) is True
        assert should_refuse_before_generation(0.55) is False


def test_should_refuse_before_generation_skips_llm_call_when_no_chunks_clear_threshold():
    """Given a query with no retrieved chunks above threshold, the caller must
    signal refusal before any LLM call is made."""
    mock_llm = MagicMock()
    best_retrieval_score = 0.0  # no relevant chunks retrieved at all

    if should_refuse_before_generation(best_retrieval_score, threshold=0.4):
        response = build_refusal_response(LegalDomain.OTHER, DISCLAIMER)
    else:
        mock_llm.invoke("some prompt built from the retrieved context")
        response = None

    mock_llm.invoke.assert_not_called()
    assert response is not None
    assert response.is_refusal is True


# --- should_refuse_after_generation -------------------------------------------


def test_should_refuse_after_generation_true_when_confidence_below_threshold():
    assert should_refuse_after_generation(0.2, threshold=0.4) is True


def test_should_refuse_after_generation_false_when_confidence_above_threshold():
    assert should_refuse_after_generation(0.7, threshold=0.4) is False


def test_should_refuse_after_generation_defaults_to_configured_threshold(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("CONFIDENCE_REFUSAL_THRESHOLD", "0.5")

    with patch("app.rag.refusal.settings", Settings(_env_file=None)):  # type: ignore[call-arg]
        assert should_refuse_after_generation(0.45) is True
        assert should_refuse_after_generation(0.55) is False


# --- build_refusal_response ---------------------------------------------------


def test_build_refusal_response_overrides_answer_with_refusal_template():
    response = build_refusal_response(LegalDomain.CRIMINAL, DISCLAIMER)

    assert response.answer == REFUSAL_TEMPLATE
    assert response.is_refusal is True
    assert response.disclaimer == DISCLAIMER
    assert response.legal_domain == LegalDomain.CRIMINAL


def test_build_refusal_response_defaults_to_no_citations_and_zero_confidence():
    response = build_refusal_response(LegalDomain.OTHER, DISCLAIMER)

    assert response.citations == []
    assert response.confidence_score == 0.0


def test_build_refusal_response_retains_low_confidence_citations_for_transparency():
    """Given a generated answer whose computed confidence is below the
    post-generation threshold, the final response must be overridden with
    the refusal template while retained low-confidence sources are still
    attached for transparency."""
    low_confidence_citations = [_citation(0.15), _citation(0.22, excerpt="Section 154 information.")]
    computed_confidence = 0.18

    assert should_refuse_after_generation(computed_confidence, threshold=0.4) is True

    response = build_refusal_response(
        LegalDomain.CRIMINAL,
        DISCLAIMER,
        citations=low_confidence_citations,
        confidence_score=computed_confidence,
    )

    assert response.answer == REFUSAL_TEMPLATE
    assert response.is_refusal is True
    assert response.citations == low_confidence_citations
    assert response.confidence_score == pytest.approx(computed_confidence)


# --- REFUSAL_TEMPLATE ----------------------------------------------------------


def test_refusal_template_recommends_consulting_a_licensed_lawyer():
    assert "licensed lawyer" in REFUSAL_TEMPLATE
