"""Unit tests for GET /api/v1/sessions/{id}/history. See TASKS.md T38."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import sessions as sessions_route
from app.main import app

EXISTING_HISTORY = [
    {"role": "user", "content": "What is the punishment for theft?"},
    {"role": "assistant", "content": "Theft is punishable under Section 379 IPC."},
    {"role": "user", "content": "What if it is a repeat offense?"},
]


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _authorize() -> None:
    async def _verify_override() -> str:
        return "valid-token"

    app.dependency_overrides[sessions_route.verify_bearer_token] = _verify_override


@pytest.mark.asyncio
async def test_returns_ordered_history_for_existing_session(monkeypatch: pytest.MonkeyPatch):
    _authorize()
    monkeypatch.setattr(sessions_route, "get_history", MagicMock(return_value=EXISTING_HISTORY))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/sessions/session-1/history",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "session-1"
    assert body["messages"] == EXISTING_HISTORY


@pytest.mark.asyncio
async def test_unknown_session_returns_empty_list_not_error(monkeypatch: pytest.MonkeyPatch):
    _authorize()
    monkeypatch.setattr(sessions_route, "get_history", MagicMock(return_value=[]))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/sessions/does-not-exist/history",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "does-not-exist"
    assert body["messages"] == []


@pytest.mark.asyncio
async def test_history_requires_valid_auth(monkeypatch: pytest.MonkeyPatch):
    service = MagicMock(return_value=EXISTING_HISTORY)
    monkeypatch.setattr(sessions_route, "get_history", service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/sessions/session-1/history")

    assert response.status_code == 401
    service.assert_not_called()
