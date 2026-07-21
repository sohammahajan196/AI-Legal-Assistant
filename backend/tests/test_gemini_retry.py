"""Tests for app.rag.gemini_retry transient-error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.rag.gemini_retry import (
    GeminiServiceUnavailableError,
    ainvoke_with_gemini_resilience,
    compute_backoff_delay,
    is_transient_gemini_error,
)


class _FakeServerError(Exception):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def test_is_transient_gemini_error_detects_503_status_code():
    assert is_transient_gemini_error(_FakeServerError("capacity", status_code=503))


def test_is_transient_gemini_error_detects_message_shape():
    err = Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
    assert is_transient_gemini_error(err)


def test_is_transient_gemini_error_rejects_other_errors():
    assert not is_transient_gemini_error(Exception("500 INTERNAL"))


def test_compute_backoff_delay_grows_exponentially():
    assert compute_backoff_delay(0, 1.0) >= 1.0
    assert compute_backoff_delay(1, 1.0) >= 2.0
    assert compute_backoff_delay(2, 1.0) >= 4.0
    assert compute_backoff_delay(3, 1.0) >= 8.0


@pytest.mark.asyncio
async def test_retries_transient_503_then_succeeds():
    llm = MagicMock()
    transient = _FakeServerError("503 UNAVAILABLE. High demand.")
    llm.ainvoke = AsyncMock(side_effect=[transient, "ok"])

    with patch("app.rag.gemini_retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        with patch("app.rag.gemini_retry.settings") as mock_settings:
            mock_settings.gemini_model = "gemini-3.5-flash"
            mock_settings.gemini_max_retries = 4
            mock_settings.gemini_retry_base_delay_seconds = 1.0
            mock_settings.gemini_fallback_model = ""
            result = await ainvoke_with_gemini_resilience(llm, "prompt", max_retries=2)

    assert result == "ok"
    assert llm.ainvoke.await_count == 2
    sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_exhausts_retries_and_raises_service_unavailable():
    llm = MagicMock()
    transient = _FakeServerError("503 UNAVAILABLE. High demand.")
    llm.ainvoke = AsyncMock(side_effect=transient)

    with patch("app.rag.gemini_retry.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(GeminiServiceUnavailableError) as exc_info:
            await ainvoke_with_gemini_resilience(llm, "prompt", max_retries=2)

    assert llm.ainvoke.await_count == 3
    assert exc_info.value.attempts == 3
    assert "temporarily busy" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_falls_back_to_secondary_model_after_primary_exhausted():
    primary = MagicMock()
    fallback = MagicMock()
    transient = _FakeServerError("503 UNAVAILABLE. High demand.")
    primary.ainvoke = AsyncMock(side_effect=transient)
    fallback.ainvoke = AsyncMock(return_value="fallback-ok")

    test_settings = Settings(
        google_api_key="test-key",
        gemini_model="gemini-3.5-flash",
        gemini_fallback_model="gemini-2.5-flash",
        gemini_max_retries=1,
        _env_file=None,  # type: ignore[call-arg]
    )

    with patch("app.rag.gemini_retry.asyncio.sleep", new_callable=AsyncMock):
        with patch("app.rag.gemini_retry.settings", test_settings):
            with patch("app.rag.llm.get_fallback_llm", return_value=fallback):
                result = await ainvoke_with_gemini_resilience(primary, "prompt")

    assert result == "fallback-ok"
    assert primary.ainvoke.await_count == 2
    fallback.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_non_transient_errors_are_not_retried():
    llm = MagicMock()
    llm.ainvoke = AsyncMock(side_effect=RuntimeError("auth failed"))

    with pytest.raises(RuntimeError, match="auth failed"):
        await ainvoke_with_gemini_resilience(llm, "prompt", max_retries=4)

    llm.ainvoke.assert_awaited_once()
