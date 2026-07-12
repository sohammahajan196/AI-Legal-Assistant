"""Unit tests for app.rag.confidence. See TASKS.md T25.

Refusal-decision tests (T26) belong in a separate module once
app.rag.refusal is implemented - kept out of this file to match the
task boundary.
"""

from __future__ import annotations

import math
from unittest.mock import patch

import pytest
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.rag.confidence import (
    compute_confidence_score,
    compute_groundedness_component,
    compute_retrieval_component,
)
from app.schemas.legal_answer import LegalDomain, SourceCitation


class BagOfWordsEmbeddings(Embeddings):
    """Deterministic offline embedder over a fixed vocabulary.

    Vectorizes text as an L2-normalized word-count vector so cosine
    similarity naturally reflects lexical overlap - lets groundedness tests
    exercise real similarity math without downloading/network-calling a real
    HuggingFace model (per testing.mdc).
    """

    def __init__(self, vocabulary: list[str]) -> None:
        self._vocab_index = {word: i for i, word in enumerate(vocabulary)}

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * len(self._vocab_index)
        for word in text.lower().split():
            idx = self._vocab_index.get(word.strip(".,;:"))
            if idx is not None:
                vec[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


VOCAB = [
    "whoever",
    "causes",
    "death",
    "by",
    "negligence",
    "shall",
    "be",
    "punished",
    "with",
    "imprisonment",
    "the",
    "cricket",
    "team",
    "scored",
    "a",
    "century",
    "in",
    "batting",
    "innings",
]


@pytest.fixture
def embedding_model() -> BagOfWordsEmbeddings:
    return BagOfWordsEmbeddings(VOCAB)


def _citation(excerpt: str, retrieval_score: float, section: str = "304A") -> SourceCitation:
    return SourceCitation(
        document="Indian Penal Code",
        act_year=1860,
        section=section,
        domain=LegalDomain.CRIMINAL,
        excerpt=excerpt,
        retrieval_score=retrieval_score,
    )


NEGLIGENCE_EXCERPT = "Whoever causes death by negligence shall be punished with imprisonment."
UNRELATED_EXCERPT = "The cricket team scored a century in the batting innings."


# --- compute_retrieval_component --------------------------------------------


def test_compute_retrieval_component_empty_citations_returns_zero():
    assert compute_retrieval_component([]) == 0.0


def test_compute_retrieval_component_averages_used_citation_scores():
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.9), _citation(NEGLIGENCE_EXCERPT, 0.7)]

    assert compute_retrieval_component(citations) == pytest.approx(0.8)


def test_compute_retrieval_component_high_when_scores_high():
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.95), _citation(NEGLIGENCE_EXCERPT, 0.98)]

    assert compute_retrieval_component(citations) > 0.9


def test_compute_retrieval_component_low_when_scores_low():
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.05), _citation(NEGLIGENCE_EXCERPT, 0.1)]

    assert compute_retrieval_component(citations) < 0.2


# --- compute_groundedness_component ------------------------------------------


def test_compute_groundedness_component_no_citations_returns_zero(embedding_model):
    assert compute_groundedness_component("some answer", [], embedding_model=embedding_model) == 0.0


def test_compute_groundedness_component_blank_answer_returns_zero(embedding_model):
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.9)]

    assert compute_groundedness_component("   ", citations, embedding_model=embedding_model) == 0.0


def test_compute_groundedness_component_high_overlap_scores_near_one(embedding_model):
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.9)]

    score = compute_groundedness_component(NEGLIGENCE_EXCERPT, citations, embedding_model=embedding_model)

    assert score == pytest.approx(1.0, abs=1e-6)


def test_compute_groundedness_component_unrelated_answer_scores_low(embedding_model):
    citations = [_citation(UNRELATED_EXCERPT, 0.9)]

    score = compute_groundedness_component(NEGLIGENCE_EXCERPT, citations, embedding_model=embedding_model)

    assert score < 0.2


def test_compute_groundedness_component_averages_across_multiple_citations(embedding_model):
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.9), _citation(UNRELATED_EXCERPT, 0.9)]

    score = compute_groundedness_component(NEGLIGENCE_EXCERPT, citations, embedding_model=embedding_model)

    assert 0.0 < score < 1.0


def test_compute_groundedness_component_defaults_to_real_embedding_model_factory():
    """Without an override, the function must fall back to the shared
    HuggingFace embedding model factory rather than requiring callers to
    always inject one."""
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.9)]

    with patch("app.rag.confidence.get_embedding_model") as mock_factory:
        mock_factory.return_value = BagOfWordsEmbeddings(VOCAB)
        compute_groundedness_component(NEGLIGENCE_EXCERPT, citations)

    mock_factory.assert_called_once_with()


# --- compute_confidence_score ------------------------------------------------


def test_compute_confidence_score_high_inputs_near_one():
    score = compute_confidence_score(0.95, 0.95, w1=0.5, w2=0.5)

    assert score > 0.9


def test_compute_confidence_score_low_inputs_near_zero():
    score = compute_confidence_score(0.05, 0.1, w1=0.5, w2=0.5)

    assert score < 0.1


def test_compute_confidence_score_uses_configured_weights_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("CONFIDENCE_RETRIEVAL_WEIGHT", "0.8")
    monkeypatch.setenv("CONFIDENCE_GROUNDEDNESS_WEIGHT", "0.2")

    with patch("app.rag.confidence.settings", Settings(_env_file=None)):  # type: ignore[call-arg]
        score = compute_confidence_score(1.0, 0.0)

    assert score == pytest.approx(0.8)


def test_compute_confidence_score_explicit_weights_override_settings():
    score = compute_confidence_score(1.0, 0.0, w1=0.1, w2=0.9)

    assert score == pytest.approx(0.1)


def test_compute_confidence_score_clamped_to_unit_interval():
    score = compute_confidence_score(1.0, 1.0, w1=0.8, w2=0.8)

    assert score == 1.0


# --- end-to-end component composition ---------------------------------------


def test_high_similarity_retrieval_and_high_overlap_answer_scores_near_one(embedding_model):
    citations = [_citation(NEGLIGENCE_EXCERPT, 0.95)]

    retrieval = compute_retrieval_component(citations)
    groundedness = compute_groundedness_component(NEGLIGENCE_EXCERPT, citations, embedding_model=embedding_model)
    confidence = compute_confidence_score(retrieval, groundedness)

    assert confidence > 0.9


def test_low_retrieval_score_and_unrelated_answer_scores_low(embedding_model):
    citations = [_citation(UNRELATED_EXCERPT, 0.05)]

    retrieval = compute_retrieval_component(citations)
    groundedness = compute_groundedness_component(NEGLIGENCE_EXCERPT, citations, embedding_model=embedding_model)
    confidence = compute_confidence_score(retrieval, groundedness)

    assert confidence < 0.15
