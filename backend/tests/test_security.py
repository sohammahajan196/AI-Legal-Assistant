"""Unit tests for app.core.security. See TASKS.md T34."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import Settings
from app.core.security import (
    get_token_tier,
    get_token_tier_mapping,
    parse_token_tier_mapping,
    reset_token_tier_mapping_cache,
    verify_bearer_token,
)


@pytest.fixture(autouse=True)
def _clear_token_mapping_cache():
    reset_token_tier_mapping_cache()
    yield
    reset_token_tier_mapping_cache()


@pytest.fixture
def auth_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    settings = Settings(
        _env_file=None,
        backend_api_tokens="valid-token:standard,premium-token:premium",
    )  # type: ignore[call-arg]
    with patch("app.core.security.settings", settings):
        reset_token_tier_mapping_cache()
        yield settings


# --- parse_token_tier_mapping ------------------------------------------------


def test_parse_token_tier_mapping_splits_comma_separated_pairs():
    mapping = parse_token_tier_mapping("alpha:standard,beta:premium")

    assert mapping == {"alpha": "standard", "beta": "premium"}


def test_parse_token_tier_mapping_rejects_malformed_entry():
    with pytest.raises(ValueError, match="expected token:tier"):
        parse_token_tier_mapping("not-a-valid-entry")


# --- verify_bearer_token -----------------------------------------------------


@pytest.mark.asyncio
async def test_valid_token_passes_through(auth_settings):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    token = await verify_bearer_token(credentials)

    assert token == "valid-token"
    assert get_token_tier(token) == "standard"


@pytest.mark.asyncio
async def test_missing_credentials_returns_401(auth_settings):
    with pytest.raises(HTTPException) as exc_info:
        await verify_bearer_token(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token"


@pytest.mark.asyncio
async def test_invalid_token_returns_401(auth_settings):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong-token")

    with pytest.raises(HTTPException) as exc_info:
        await verify_bearer_token(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid bearer token"


@pytest.mark.asyncio
async def test_malformed_non_bearer_scheme_returns_401(auth_settings):
    credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="valid-token")

    with pytest.raises(HTTPException) as exc_info:
        await verify_bearer_token(credentials)

    assert exc_info.value.status_code == 401
    assert "Bearer" in exc_info.value.detail


# --- mapping loaded from settings ---------------------------------------------


def test_token_mapping_is_loaded_from_settings_not_hardcoded(auth_settings):
    mapping = get_token_tier_mapping()

    assert mapping == {"valid-token": "standard", "premium-token": "premium"}


def test_different_settings_produce_different_mapping(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    first = Settings(_env_file=None, backend_api_tokens="token-a:standard")  # type: ignore[call-arg]
    with patch("app.core.security.settings", first):
        reset_token_tier_mapping_cache()
        assert get_token_tier_mapping() == {"token-a": "standard"}

    second = Settings(_env_file=None, backend_api_tokens="token-b:premium")  # type: ignore[call-arg]
    with patch("app.core.security.settings", second):
        reset_token_tier_mapping_cache()
        assert get_token_tier_mapping() == {"token-b": "premium"}
