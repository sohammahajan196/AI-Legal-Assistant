"""Unit tests for app.rag.cache. See TASKS.md T32."""

from __future__ import annotations

import math
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
from langchain_core.embeddings import Embeddings

from app.core.config import Settings
from app.rag.cache import (
    get_cached_response,
    normalize_query,
    ping_redis,
    reset_redis_client,
    set_cached_response,
)
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain

SAMPLE_RESPONSE = LegalAnswerResponse(
    answer="Theft is punishable under Section 379 IPC.",
    confidence_score=0.85,
    legal_domain=LegalDomain.CRIMINAL,
    citations=[],
    is_refusal=False,
    disclaimer="This is not legal advice.",
)


class FixedVectorEmbeddings(Embeddings):
    """Deterministic embedder returning a preconfigured vector per exact query
    string -- lets semantic-cache tests control cosine similarity without any
    real model download or network call (per testing.mdc)."""

    def __init__(self, vectors_by_query: dict[str, list[float]]) -> None:
        self._vectors_by_query = vectors_by_query

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if text not in self._vectors_by_query:
            raise KeyError(f"No fixed embedding configured for query: {text!r}")
        return self._vectors_by_query[text]


def _near_duplicate_vector(base: list[float], epsilon: float = 0.01) -> list[float]:
    """Build a vector with cosine similarity > 0.95 to `base`."""
    perturbed = [value + epsilon for value in base]
    norm = math.sqrt(sum(v * v for v in perturbed))
    return [v / norm for v in perturbed]


@pytest.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    reset_redis_client()

    async def _return_fake_client():
        return client

    with patch("app.rag.cache._get_redis_client", _return_fake_client):
        yield client

    await client.aclose()
    reset_redis_client()


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    settings = Settings(_env_file=None, cache_ttl_seconds=60, cache_semantic_similarity_threshold=0.95)  # type: ignore[call-arg]
    with patch("app.rag.cache.settings", settings):
        yield settings


# --- exact-match cache --------------------------------------------------------


@pytest.mark.asyncio
async def test_exact_match_store_then_fetch_returns_cached_response(fake_redis, test_settings):
    query = "What is the punishment for theft?"
    await set_cached_response(query, "layperson", SAMPLE_RESPONSE)

    cached = await get_cached_response(query, "layperson")

    assert cached is not None
    assert cached == SAMPLE_RESPONSE


@pytest.mark.asyncio
async def test_exact_match_normalizes_whitespace_and_case(fake_redis, test_settings):
    await set_cached_response("  What Is THEFT?  ", "layperson", SAMPLE_RESPONSE)

    cached = await get_cached_response("what is theft?", "layperson")

    assert cached == SAMPLE_RESPONSE


@pytest.mark.asyncio
async def test_exact_match_is_scoped_by_user_type(fake_redis, test_settings):
    await set_cached_response("What is theft?", "layperson", SAMPLE_RESPONSE)

    cached = await get_cached_response("What is theft?", "lawyer")

    assert cached is None


# --- semantic near-duplicate cache -------------------------------------------


@pytest.mark.asyncio
async def test_semantic_near_duplicate_hits_cache_with_fixed_embeddings(fake_redis, test_settings):
    original_query = "What is the punishment for theft under IPC?"
    paraphrase = "What penalty applies to theft under the Indian Penal Code?"
    base_vector = [1.0, 0.0, 0.0]
    embedding_model = FixedVectorEmbeddings(
        {
            original_query: base_vector,
            paraphrase: _near_duplicate_vector(base_vector),
        }
    )

    await set_cached_response(
        original_query, "layperson", SAMPLE_RESPONSE, embedding_model=embedding_model
    )

    cached = await get_cached_response(
        paraphrase, "layperson", embedding_model=embedding_model
    )

    assert cached == SAMPLE_RESPONSE


@pytest.mark.asyncio
async def test_semantic_lookup_does_not_hit_when_similarity_below_threshold(fake_redis, test_settings):
    original_query = "What is theft?"
    unrelated_query = "How do I bake a cake?"
    embedding_model = FixedVectorEmbeddings(
        {
            original_query: [1.0, 0.0, 0.0],
            unrelated_query: [0.0, 1.0, 0.0],
        }
    )

    await set_cached_response(
        original_query, "layperson", SAMPLE_RESPONSE, embedding_model=embedding_model
    )

    cached = await get_cached_response(
        unrelated_query, "layperson", embedding_model=embedding_model
    )

    assert cached is None


# --- graceful degradation when Redis is unreachable --------------------------


@pytest.mark.asyncio
async def test_get_cached_response_returns_none_when_redis_unreachable(test_settings, caplog):
    async def _raise_connection_error():
        raise ConnectionError("Redis unreachable")

    reset_redis_client()
    with patch("app.rag.cache._get_redis_client", _raise_connection_error):
        with caplog.at_level("WARNING"):
            cached = await get_cached_response("What is theft?", "layperson")

    assert cached is None
    assert any("Cache lookup failed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_set_cached_response_does_not_raise_when_redis_unreachable(test_settings, caplog):
    async def _raise_connection_error():
        raise ConnectionError("Redis unreachable")

    reset_redis_client()
    with patch("app.rag.cache._get_redis_client", _raise_connection_error):
        with caplog.at_level("WARNING"):
            await set_cached_response("What is theft?", "layperson", SAMPLE_RESPONSE)

    assert any("Cache store failed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_ping_redis_returns_true_when_ping_succeeds(test_settings):
    fake_client = AsyncMock()
    fake_client.ping = AsyncMock(return_value=True)
    fake_client.aclose = AsyncMock()

    with patch("app.rag.cache.aioredis.from_url", return_value=fake_client):
        assert await ping_redis() is True

    fake_client.ping.assert_awaited_once()
    fake_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_ping_redis_returns_false_when_unreachable(test_settings, caplog):
    with patch(
        "app.rag.cache.aioredis.from_url",
        side_effect=ConnectionError("Redis unreachable"),
    ):
        with caplog.at_level("WARNING"):
            assert await ping_redis() is False

    assert any("Redis health PING failed" in record.message for record in caplog.records)


# --- helpers ------------------------------------------------------------------


def test_normalize_query_lowercases_and_collapses_whitespace():
    assert normalize_query("  What   Is   Theft?  ") == "what is theft?"
