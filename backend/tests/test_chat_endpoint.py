"""Unit tests for POST /api/v1/chat. See TASKS.md T37."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from app.api.routes import chat as chat_route
from app.main import app
from app.rag.exceptions import INDEX_BUILD_HINT, RetrievalIndexNotFoundError
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain, SourceCitation


SAMPLE_RESPONSE = LegalAnswerResponse(
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


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _authorize_as(token: str = "valid-token") -> None:
    async def _verify_override() -> str:
        return token

    app.dependency_overrides[chat_route.verify_bearer_token] = _verify_override


@pytest.fixture(autouse=True)
def _use_memory_rate_limit_storage():
    """Avoid Redis connection timeouts in endpoint tests.

    T35 separately verifies Redis-backed limiter construction/behavior. These
    T37 tests focus on endpoint wiring and async request handling.
    """
    storage = MemoryStorage()
    chat_route.limiter._storage = storage
    chat_route.limiter._limiter = FixedWindowRateLimiter(storage)
    chat_route.limiter._storage_dead = False
    yield


@pytest.mark.asyncio
async def test_authenticated_chat_returns_legal_answer_response(monkeypatch: pytest.MonkeyPatch):
    _authorize_as()
    chat_service = AsyncMock(return_value=SAMPLE_RESPONSE)
    query_logger = MagicMock()
    monkeypatch.setattr(chat_route, "handle_chat_request", chat_service)
    monkeypatch.setattr(chat_route, "log_query", query_logger)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "query": "What is the punishment for theft?",
                "session_id": "session-1",
                "user_type": "layperson",
                "consent_to_log": True,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == SAMPLE_RESPONSE.answer
    assert body["confidence_score"] == SAMPLE_RESPONSE.confidence_score
    assert body["legal_domain"] == SAMPLE_RESPONSE.legal_domain.value
    assert body["is_refusal"] is False
    assert body["citations"][0]["document"] == "Indian Penal Code"

    chat_service.assert_awaited_once_with(
        "What is the punishment for theft?",
        "session-1",
        "layperson",
    )
    query_logger.assert_called_once()
    _, log_kwargs = query_logger.call_args
    assert log_kwargs["query"] == "What is the punishment for theft?"
    assert log_kwargs["consent_to_log"] is True
    assert log_kwargs["retrieved_chunk_ids"] == ["Indian Penal Code, S.379"]
    assert log_kwargs["confidence_score"] == SAMPLE_RESPONSE.confidence_score


@pytest.mark.asyncio
async def test_unauthenticated_chat_returns_401_before_service_call(monkeypatch: pytest.MonkeyPatch):
    chat_service = AsyncMock(return_value=SAMPLE_RESPONSE)
    monkeypatch.setattr(chat_route, "handle_chat_request", chat_service)
    monkeypatch.setattr(chat_route, "log_query", MagicMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"query": "What is theft?", "user_type": "layperson"},
        )

    assert response.status_code == 401
    chat_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_chat_endpoint_awaits_service_without_serializing_requests(
    monkeypatch: pytest.MonkeyPatch,
):
    _authorize_as()

    async def _slow_chat_service(query: str, session_id: str | None, user_type: str) -> LegalAnswerResponse:
        await asyncio.sleep(0.05)
        return SAMPLE_RESPONSE

    chat_service = AsyncMock(side_effect=_slow_chat_service)
    monkeypatch.setattr(chat_route, "handle_chat_request", chat_service)
    monkeypatch.setattr(chat_route, "log_query", MagicMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        responses = await asyncio.gather(
            *[
                client.post(
                    "/api/v1/chat",
                    headers={"Authorization": f"Bearer token-{i}"},
                    json={"query": f"What is theft? {i}", "user_type": "layperson"},
                )
                for i in range(5)
            ]
        )
        elapsed = time.perf_counter() - started

    assert all(response.status_code == 200 for response in responses)
    assert chat_service.await_count == 5
    # Five 50ms requests would take about 250ms if the endpoint serialized them.
    assert elapsed < 0.2


@pytest.mark.asyncio
async def test_chat_returns_503_when_retrieval_indices_missing(
    monkeypatch: pytest.MonkeyPatch,
):
    """Missing FAISS/BM25 artifacts must surface as a clear 503, not a raw 500."""
    _authorize_as()
    monkeypatch.setattr(
        chat_route,
        "handle_chat_request",
        AsyncMock(
            side_effect=RetrievalIndexNotFoundError(
                "FAISS",
                "./data/faiss_index",
                "'index.faiss' and 'index.pkl'",
            )
        ),
    )
    monkeypatch.setattr(chat_route, "log_query", MagicMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            headers={"Authorization": "Bearer valid-token"},
            json={"query": "What is theft?", "user_type": "layperson"},
        )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "FAISS index not found" in detail
    assert INDEX_BUILD_HINT in detail
