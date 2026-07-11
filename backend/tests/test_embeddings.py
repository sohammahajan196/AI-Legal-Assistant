"""Unit tests for app.rag.embeddings. See TASKS.md T14."""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Settings
from app.rag.embeddings import (
    BGE_BASE_EN_V1_5_DIMENSION,
    expected_embedding_dimension,
    get_embedding_model,
    reset_embedding_model_cache,
)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@pytest.fixture(autouse=True)
def _clear_embedding_cache():
    reset_embedding_model_cache()
    yield
    reset_embedding_model_cache()


def test_get_embedding_model_uses_settings_model_name(monkeypatch: pytest.MonkeyPatch):
    """Factory must pass the config-driven model name to HuggingFaceEmbeddings."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "custom/sentence-model")

    with patch("app.rag.embeddings.settings", Settings(_env_file=None)) as mock_settings:  # type: ignore[call-arg]
        with patch("app.rag.embeddings.HuggingFaceEmbeddings") as mock_cls:
            mock_cls.return_value = MagicMock()
            get_embedding_model()

    mock_cls.assert_called_once_with(
        model_name="custom/sentence-model",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    assert mock_settings.embedding_model == "custom/sentence-model"


def test_get_embedding_model_caches_per_model_name():
    """Repeated calls for the same model must reuse the cached instance."""
    with patch("app.rag.embeddings.HuggingFaceEmbeddings") as mock_cls:
        sentinel = MagicMock()
        mock_cls.return_value = sentinel

        first = get_embedding_model("BAAI/bge-base-en-v1.5")
        second = get_embedding_model("BAAI/bge-base-en-v1.5")

    assert first is second
    mock_cls.assert_called_once()


def test_expected_embedding_dimension_for_default_model():
    assert expected_embedding_dimension("BAAI/bge-base-en-v1.5") == BGE_BASE_EN_V1_5_DIMENSION


def test_embed_query_returns_expected_dimension():
    """A sample sentence must embed to the bge-base-en-v1.5 vector size (768)."""
    model = get_embedding_model("BAAI/bge-base-en-v1.5")
    vector = model.embed_query("Section 304A deals with death by negligence.")

    assert isinstance(vector, list)
    assert len(vector) == BGE_BASE_EN_V1_5_DIMENSION
    assert all(isinstance(value, float) for value in vector)


def test_similar_sentences_have_higher_cosine_similarity_than_unrelated():
    """Semantically related legal phrases should score higher than unrelated text."""
    model = get_embedding_model("BAAI/bge-base-en-v1.5")

    similar_a = "Section 304A punishes causing death by negligence."
    similar_b = "Negligent acts causing death are covered under Section 304A."
    unrelated_a = "The Transfer of Property Act governs immovable property transfers."
    unrelated_b = "Consumer courts hear complaints about defective goods."

    vec_similar_a = model.embed_query(similar_a)
    vec_similar_b = model.embed_query(similar_b)
    vec_unrelated_a = model.embed_query(unrelated_a)
    vec_unrelated_b = model.embed_query(unrelated_b)

    similar_score = _cosine_similarity(vec_similar_a, vec_similar_b)
    unrelated_score = _cosine_similarity(vec_unrelated_a, vec_unrelated_b)

    assert similar_score > unrelated_score


def test_invalid_model_name_raises():
    """An unknown model id must fail loudly instead of returning a broken embedder."""
    with pytest.raises(Exception):
        model = get_embedding_model("this-model-does-not-exist-xyz")
        model.embed_query("test sentence")
