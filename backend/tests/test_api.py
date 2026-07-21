"""FastAPI integration tests. See TASKS.md T40."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from app.api.routes import chat as chat_route
from app.core.config import Settings
from app.core.rate_limit import reset_rate_limit_tier_mapping_cache
from app.core.security import reset_token_tier_mapping_cache
from app.main import app
from app.rag.cache import reset_redis_client
from app.rag.refusal import REFUSAL_TEMPLATE
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain, SourceCitation
from app.services import session_store

VALID_TOKEN = "integration-token"
AUTH_HEADERS = {"Authorization": f"Bearer {VALID_TOKEN}"}

HAPPY_RESPONSE = LegalAnswerResponse(
    answer="Theft is punishable under Section 379 IPC.",
    confidence_score=0.87,
    legal_domain=LegalDomain.CRIMINAL,
    citations=[
        SourceCitation(
            document="Indian Penal Code",
            act_year=1860,
            section="379",
            domain=LegalDomain.CRIMINAL,
            excerpt="Whoever commits theft shall be punished...",
            retrieval_score=0.91,
        )
    ],
    is_refusal=False,
    disclaimer="This is not a substitute for licensed legal counsel.",
)

REFUSAL_RESPONSE = LegalAnswerResponse(
    answer=REFUSAL_TEMPLATE,
    confidence_score=0.08,
    legal_domain=LegalDomain.OTHER,
    citations=[],
    is_refusal=True,
    disclaimer="This is not a substitute for licensed legal counsel.",
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _memory_rate_limit_storage():
    """Keep rate-limit tests off real Redis (see testing.mdc)."""
    storage = MemoryStorage()
    chat_route.limiter._storage = storage
    chat_route.limiter._limiter = FixedWindowRateLimiter(storage)
    chat_route.limiter._storage_dead = False
    yield


@pytest.fixture
def integration_settings(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Shared auth/rate-limit/session config for end-to-end API tests."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    db_path = tmp_path / "integration.db"
    settings = Settings(
        _env_file=None,
        backend_api_tokens=f"{VALID_TOKEN}:standard",
        rate_limit_tier_limits="standard:2",
        rate_limit_per_minute=2,
        sqlite_db_path=str(db_path),
        cache_ttl_seconds=60,
    )  # type: ignore[call-arg]

    reset_token_tier_mapping_cache()
    reset_rate_limit_tier_mapping_cache()
    session_store.reset_session_store()
    reset_redis_client()

    with (
        patch("app.core.security.settings", settings),
        patch("app.core.rate_limit.settings", settings),
        patch("app.api.routes.chat.settings", settings),
        patch("app.services.session_store.settings", settings),
    ):
        yield settings

    session_store.reset_session_store()
    reset_token_tier_mapping_cache()
    reset_rate_limit_tier_mapping_cache()
    reset_redis_client()


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
def mock_rag_chain():
    chain_mock = AsyncMock(return_value=HAPPY_RESPONSE)
    with patch("app.services.chat_service.run_rag_chain", chain_mock):
        yield chain_mock


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.mark.asyncio
async def test_unauthenticated_chat_returns_401(client, integration_settings, mock_rag_chain):
    response = await client.post(
        "/api/v1/chat",
        json={"query": "What is theft?", "user_type": "layperson"},
    )

    assert response.status_code == 401
    mock_rag_chain.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limit_exceeded_returns_429(client, integration_settings, mock_rag_chain):
    async def _post(query: str):
        return await client.post(
            "/api/v1/chat",
            headers=AUTH_HEADERS,
            json={"query": query, "user_type": "layperson"},
        )

    assert (await _post("What is theft? 1")).status_code == 200
    assert (await _post("What is theft? 2")).status_code == 200
    response = await _post("What is theft? 3")

    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    assert mock_rag_chain.await_count == 2


@pytest.mark.asyncio
async def test_chat_happy_path_returns_legal_answer_response(
    client,
    integration_settings,
    fake_redis,
    mock_rag_chain,
):
    response = await client.post(
        "/api/v1/chat",
        headers=AUTH_HEADERS,
        json={
            "query": "What is the punishment for theft?",
            "user_type": "layperson",
            "consent_to_log": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == HAPPY_RESPONSE.answer
    assert body["confidence_score"] == HAPPY_RESPONSE.confidence_score
    assert body["legal_domain"] == HAPPY_RESPONSE.legal_domain.value
    assert body["is_refusal"] is False
    assert body["disclaimer"] == HAPPY_RESPONSE.disclaimer
    assert body["citations"][0]["document"] == "Indian Penal Code"
    mock_rag_chain.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_refusal_response_shape(client, integration_settings, fake_redis):
    refusal_chain = AsyncMock(return_value=REFUSAL_RESPONSE)
    with patch("app.services.chat_service.run_rag_chain", refusal_chain):
        response = await client.post(
            "/api/v1/chat",
            headers=AUTH_HEADERS,
            json={"query": "Obscure niche legal question?", "user_type": "lawyer"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["is_refusal"] is True
    assert body["answer"] == REFUSAL_TEMPLATE
    assert body["disclaimer"] == REFUSAL_RESPONSE.disclaimer
    assert body["citations"] == []
    assert 0 <= body["confidence_score"] <= 1


@pytest.mark.asyncio
async def test_session_history_round_trip(client, integration_settings, fake_redis, mock_rag_chain):
    session_id = session_store.create_session()
    query = "What is the punishment for theft?"

    chat_response = await client.post(
        "/api/v1/chat",
        headers=AUTH_HEADERS,
        json={
            "query": query,
            "session_id": session_id,
            "user_type": "layperson",
        },
    )
    history_response = await client.get(
        f"/api/v1/sessions/{session_id}/history",
        headers=AUTH_HEADERS,
    )

    assert chat_response.status_code == 200
    assert history_response.status_code == 200

    history = history_response.json()
    assert history["session_id"] == session_id
    assert history["messages"] == [
        {"role": "user", "content": query},
        {"role": "assistant", "content": HAPPY_RESPONSE.answer},
    ]
    mock_rag_chain.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_check_returns_200_without_auth(client, integration_settings):
    with patch("app.api.routes.health.ping_redis", new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = True
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "ok"}
    mock_ping.assert_awaited_once()
