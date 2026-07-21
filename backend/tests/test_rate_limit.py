"""Unit tests for app.core.rate_limit. See TASKS.md T35."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from app.core.config import Settings
from app.core.rate_limit import (
    create_limiter,
    get_rate_limit_string,
    get_rate_limit_tier_mapping,
    get_requests_per_minute_for_tier,
    parse_rate_limit_tier_limits,
    register_rate_limiting,
    reset_limiter,
    reset_rate_limit_tier_mapping_cache,
)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    reset_limiter()
    reset_rate_limit_tier_mapping_cache()
    yield
    reset_limiter()
    reset_rate_limit_tier_mapping_cache()


@pytest.fixture
def rate_limit_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    settings = Settings(
        _env_file=None,
        backend_api_tokens="token-a:standard,token-b:premium",
        rate_limit_tier_limits="standard:2,premium:5",
        rate_limit_per_minute=2,
    )  # type: ignore[call-arg]
    with patch("app.core.security.settings", settings), patch("app.core.rate_limit.settings", settings):
        reset_rate_limit_tier_mapping_cache()
        yield settings


def _build_rate_limited_client(
    rate_limit_settings: Settings,
    *,
    limit_value: str | None = None,
) -> TestClient:
    app = FastAPI()
    limiter = create_limiter(storage_uri="memory://")
    register_rate_limiting(app, limiter)

    resolved_limit = limit_value or get_rate_limit_string

    @app.get("/limited")
    @limiter.limit(resolved_limit)
    async def limited(request: Request) -> JSONResponse:
        return JSONResponse({"ok": "true"})

    return TestClient(app)


@pytest.fixture
def client(rate_limit_settings: Settings) -> TestClient:
    return _build_rate_limited_client(rate_limit_settings)


# --- exceeding configured rate returns 429 -------------------------------------


def test_exceeding_configured_rate_returns_429_with_clear_error_body(client: TestClient):
    headers = {"Authorization": "Bearer token-a"}

    assert client.get("/limited", headers=headers).status_code == 200
    assert client.get("/limited", headers=headers).status_code == 200

    response = client.get("/limited", headers=headers)

    assert response.status_code == 429
    body = response.json()
    assert "detail" in body
    assert "Rate limit exceeded" in body["detail"]


# --- independent counters per token ------------------------------------------


def test_different_tokens_have_independent_rate_limit_counters(client: TestClient):
    headers_a = {"Authorization": "Bearer token-a"}
    headers_b = {"Authorization": "Bearer token-b"}

    assert client.get("/limited", headers=headers_a).status_code == 200
    assert client.get("/limited", headers=headers_a).status_code == 200
    assert client.get("/limited", headers=headers_a).status_code == 429

    assert client.get("/limited", headers=headers_b).status_code == 200


# --- window reset --------------------------------------------------------------


def test_rate_limit_resets_after_configured_window(rate_limit_settings: Settings):
    client = _build_rate_limited_client(rate_limit_settings, limit_value="2/second")
    headers = {"Authorization": "Bearer token-a"}

    assert client.get("/limited", headers=headers).status_code == 200
    assert client.get("/limited", headers=headers).status_code == 200
    assert client.get("/limited", headers=headers).status_code == 429

    time.sleep(1.1)

    assert client.get("/limited", headers=headers).status_code == 200


# --- tier limits loaded from settings ------------------------------------------


def test_parse_rate_limit_tier_limits_splits_pairs():
    assert parse_rate_limit_tier_limits("standard:30,premium:100") == {
        "standard": 30,
        "premium": 100,
    }


def test_tier_limits_are_loaded_from_settings_not_hardcoded(rate_limit_settings: Settings):
    mapping = get_rate_limit_tier_mapping()

    assert mapping == {"standard": 2, "premium": 5}
    assert get_requests_per_minute_for_tier("standard") == 2
    assert get_requests_per_minute_for_tier("premium") == 5
    assert get_requests_per_minute_for_tier("unknown") == rate_limit_settings.rate_limit_per_minute


def test_create_limiter_falls_back_to_memory_when_redis_unreachable(rate_limit_settings, caplog):
    with patch("app.core.rate_limit._check_redis_reachable", return_value=False):
        with caplog.at_level("WARNING"):
            limiter = create_limiter(storage_uri="redis://localhost:6379/0")

    storage_uri = getattr(limiter, "_storage_uri", None) or getattr(limiter, "storage_uri", "")
    assert "memory" in str(storage_uri)
    assert any("falling back to in-memory storage" in record.message for record in caplog.records)


def test_create_limiter_skips_reachability_probe_for_memory_uri(rate_limit_settings):
    with patch("app.core.rate_limit._check_redis_reachable") as check:
        limiter = create_limiter(storage_uri="memory://")

    check.assert_not_called()
    storage_uri = getattr(limiter, "_storage_uri", None) or getattr(limiter, "storage_uri", "")
    assert "memory" in str(storage_uri)