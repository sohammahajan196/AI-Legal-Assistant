"""Unit tests for app.core.config.Settings. See TASKS.md T03."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings, _BACKEND_ROOT, _REPO_ROOT, default_env_files


def test_settings_loads_with_required_secret_present():
    """Settings() succeeds and applies documented defaults when the required
    secret is supplied."""
    settings = Settings(google_api_key="a-real-looking-key", _env_file=None)  # type: ignore[call-arg]

    assert settings.google_api_key.get_secret_value() == "a-real-looking-key"
    assert settings.gemini_model == "gemini-3.5-flash"
    assert settings.embedding_model == "BAAI/bge-base-en-v1.5"
    assert settings.confidence_refusal_threshold == 0.4
    assert settings.confidence_caution_threshold == 0.6
    assert settings.rate_limit_per_minute == 30
    assert settings.gemini_max_retries == 4
    assert settings.gemini_retry_base_delay_seconds == 1.0
    assert settings.gemini_fallback_model == ""


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


def test_default_env_files_are_absolute_and_cwd_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """``.env`` discovery must not depend on the process working directory."""
    monkeypatch.chdir(tmp_path)

    env_files = default_env_files()

    assert env_files == (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env")
    assert all(path.is_absolute() for path in env_files)


def test_settings_loads_repo_root_env_when_cwd_is_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A root-only ``.env`` is honored even when uvicorn is started outside backend/."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.chdir(tmp_path)

    root_env = tmp_path / "repo-root.env"
    root_env.write_text(
        "GOOGLE_API_KEY=from-root-env-file\nGEMINI_MODEL=gemini-from-file\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=root_env)  # type: ignore[call-arg]

    assert settings.google_api_key.get_secret_value() == "from-root-env-file"
    assert settings.gemini_model == "gemini-from-file"
