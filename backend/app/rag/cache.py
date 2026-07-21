"""
Response caching: Redis exact-match cache + semantic near-duplicate query cache.

See PLAN.md Section 9 and TASKS.md T32.
"""

from __future__ import annotations

import hashlib
import json
import math

import redis.asyncio as aioredis
from langchain_core.embeddings import Embeddings

from app.core.config import settings
from app.core.logging import logger
from app.rag.embeddings import get_embedding_model
from app.schemas.legal_answer import LegalAnswerResponse

_EXACT_KEY_PREFIX = "legal_assistant:cache:exact:"
_SEMANTIC_KEY_PREFIX = "legal_assistant:cache:semantic:"

_redis_client: aioredis.Redis | None = None


def normalize_query(query: str) -> str:
    """Normalize a query for exact-match cache keying."""
    return " ".join(query.strip().lower().split())


def _exact_cache_key(normalized_query: str, user_type: str) -> str:
    digest = hashlib.sha256(f"{normalized_query}|{user_type}".encode()).hexdigest()
    return f"{_EXACT_KEY_PREFIX}{digest}"


def _semantic_index_key(user_type: str) -> str:
    return f"{_SEMANTIC_KEY_PREFIX}{user_type}"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _get_redis_client() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def reset_redis_client() -> None:
    """Clear the cached Redis client singleton (for tests)."""
    global _redis_client
    _redis_client = None


async def ping_redis(*, timeout: float = 0.5) -> bool:
    """Return True if Redis accepts a PING within *timeout* seconds.

    Uses a short-lived client (not the cache singleton) so a health probe
    never poisons or closes the shared connection used by request caching.
    """
    client = None
    try:
        client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        return bool(await client.ping())
    except Exception as exc:
        logger.warning(
            "Redis health PING failed (%s): %s",
            type(exc).__name__,
            exc,
        )
        return False
    finally:
        if client is not None:
            await client.aclose()


def _embed_query(query: str, embedding_model: Embeddings | None = None) -> list[float]:
    model = embedding_model or get_embedding_model()
    return model.embed_query(query)


async def _find_semantic_match(
    client: aioredis.Redis,
    query: str,
    user_type: str,
    embedding_model: Embeddings | None = None,
) -> str | None:
    """Return the exact-cache key for a near-duplicate query, if any."""
    raw_entries = await client.lrange(_semantic_index_key(user_type), 0, -1)
    if not raw_entries:
        return None

    query_vector = _embed_query(query, embedding_model=embedding_model)
    threshold = settings.cache_semantic_similarity_threshold

    best_key: str | None = None
    best_similarity = threshold

    for raw_entry in raw_entries:
        entry = json.loads(raw_entry)
        similarity = _cosine_similarity(query_vector, entry["embedding"])
        if similarity > best_similarity:
            best_similarity = similarity
            best_key = entry["response_key"]

    return best_key


async def get_cached_response(
    query: str,
    user_type: str,
    *,
    embedding_model: Embeddings | None = None,
) -> LegalAnswerResponse | None:
    """Return a cached response if one exists for this (or a near-duplicate)
    query, else None.

    Degrades gracefully (returns None) if Redis is unreachable, per
    database.mdc.
    """
    normalized = normalize_query(query)
    try:
        client = await _get_redis_client()

        exact_key = _exact_cache_key(normalized, user_type)
        cached = await client.get(exact_key)
        if cached is not None:
            return LegalAnswerResponse.model_validate_json(cached)

        semantic_key = await _find_semantic_match(
            client, query, user_type, embedding_model=embedding_model
        )
        if semantic_key is None:
            return None

        cached = await client.get(semantic_key)
        if cached is None:
            return None
        return LegalAnswerResponse.model_validate_json(cached)
    except Exception as exc:
        logger.exception("Cache lookup failed: %s", type(exc).__name__)
        return None


async def set_cached_response(
    query: str,
    user_type: str,
    response: LegalAnswerResponse,
    *,
    embedding_model: Embeddings | None = None,
) -> None:
    """Store a response in the cache with a configured TTL.

    Also records the query embedding for semantic near-duplicate lookup.
    Degrades gracefully (logs a warning, no-op) if Redis is unreachable,
    per database.mdc.
    """
    normalized = normalize_query(query)
    try:
        client = await _get_redis_client()
        exact_key = _exact_cache_key(normalized, user_type)
        payload = response.model_dump_json()

        await client.set(exact_key, payload, ex=settings.cache_ttl_seconds)

        semantic_entry = json.dumps(
            {
                "response_key": exact_key,
                "embedding": _embed_query(query, embedding_model=embedding_model),
            }
        )
        semantic_key = _semantic_index_key(user_type)
        await client.lpush(semantic_key, semantic_entry)
        await client.ltrim(semantic_key, 0, settings.cache_semantic_max_entries - 1)
        await client.expire(semantic_key, settings.cache_ttl_seconds)
    except Exception as exc:
        logger.exception("Cache store failed: %s", type(exc).__name__)


async def close_redis_client() -> None:
    """Close the cached Redis client (for app shutdown / tests)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
