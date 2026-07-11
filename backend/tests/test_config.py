"""Unit tests for app.core.config.Settings. See TASKS.md T03."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_with_required_secret_present():
    """Settings() succeeds and applies documented defaults when the required
    secret is supplied."""
    settings = Settings(google_api_key="a-real-looking-key", _env_file=None)  # type: ignore[call-arg]

    assert settings.google_api_key.get_secret_value() == "a-real-looking-key"
    assert settings.gemini_model == "gemini-2.5-flash"
    assert settings.embedding_model == "BAAI/bge-base-en-v1.5"
    assert settings.confidence_refusal_threshold == 0.4
    assert settings.confidence_caution_threshold == 0.6
    assert settings.rate_limit_per_minute == 30


def test_settings_overrides_defaults_from_env(monkeypatch: pytest.MonkeyPatch):
    """Explicit env vars override the documented defaults."""
    monkeypatch.setenv("GOOGLE_API_KEY", "env-supplied-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "99")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.google_api_key.get_secret_value() == "env-supplied-key"
    assert settings.gemini_model == "gemini-2.5-pro"
    assert settings.rate_limit_per_minute == 99


def test_settings_missing_google_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch):
    """A missing GOOGLE_API_KEY must fail loudly, not silently default to None/empty."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)  # type: ignore[call-arg]

    assert "google_api_key" in str(exc_info.value)


def test_settings_blank_google_api_key_raises_clear_error():
    """An explicitly blank GOOGLE_API_KEY (e.g. `GOOGLE_API_KEY=` in .env) must
    also fail loudly rather than being treated as a valid empty credential."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(google_api_key="   ", _env_file=None)  # type: ignore[call-arg]

    assert "must not be blank" in str(exc_info.value)


def test_settings_secret_not_leaked_in_repr():
    """The API key must not appear in plain text if Settings is ever logged/printed."""
    settings = Settings(google_api_key="super-secret-value", _env_file=None)  # type: ignore[call-arg]

    assert "super-secret-value" not in repr(settings)
    assert "super-secret-value" not in str(settings)
