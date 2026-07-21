"""Unit tests for GET /api/v1/domains and GET /api/v1/health. See TASKS.md T39."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes import domains as domains_route
from app.main import app
from app.schemas.legal_answer import LegalDomain, supported_domains

EXPECTED_DOMAINS = [
    {"value": domain.value, "label": label}
    for domain, label in supported_domains()
]


@pytest.fixture(autouse=True)
def _clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_redis_health_ping():
    """Health must not hit a real Redis instance (testing.mdc)."""
    with patch("app.api.routes.health.ping_redis", new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = True
        yield mock_ping


def _authorize() -> None:
    async def _verify_override() -> str:
        return "valid-token"

    app.dependency_overrides[domains_route.verify_bearer_token] = _verify_override


@pytest.mark.asyncio
async def test_domains_returns_six_configured_domains_with_labels():
    _authorize()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/domains",
            headers={"Authorization": "Bearer valid-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["domains"] == EXPECTED_DOMAINS
    assert len(body["domains"]) == 6
    assert LegalDomain.OTHER.value not in {item["value"] for item in body["domains"]}


@pytest.mark.asyncio
async def test_domains_requires_valid_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/domains")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_returns_200_without_bearer_token(_mock_redis_health_ping):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "ok"}
    _mock_redis_health_ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_health_reports_degraded_when_redis_unavailable(_mock_redis_health_ping):
    _mock_redis_health_ping.return_value = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "redis": "unavailable"}


@pytest.mark.asyncio
async def test_domains_and_health_respond_quickly():
    _authorize()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        started = time.perf_counter()
        domains_response, health_response = await asyncio.gather(
            client.get(
                "/api/v1/domains",
                headers={"Authorization": "Bearer valid-token"},
            ),
            client.get("/api/v1/health"),
        )
        elapsed = time.perf_counter() - started

    assert domains_response.status_code == 200
    assert health_response.status_code == 200
    # T39: no heavy dependencies on the request path — both should be near-instant.
    assert elapsed < 0.05
