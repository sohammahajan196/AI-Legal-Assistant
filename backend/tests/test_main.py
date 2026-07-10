"""Unit tests for the FastAPI app skeleton. See TASKS.md T02."""

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


def test_root_returns_200():
    """`GET /` boots the app and responds with 200 (T02 acceptance criterion)."""
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200


def test_root_returns_expected_body():
    """The root route reports the app name and an ok status."""
    client = TestClient(app)

    response = client.get("/")
    body = response.json()

    assert body == {"name": "AI Legal Assistant API", "status": "ok"}


def test_root_response_is_json():
    """The root route responds with a JSON content type, not plain text/HTML."""
    client = TestClient(app)

    response = client.get("/")

    assert response.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_root_returns_200_async():
    """The root route is reachable via an async client (no blocking startup issues)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
