"""Unit tests for app.rag.llm. See TASKS.md T22."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.core.config import Settings
from app.rag.llm import get_llm, reset_llm_cache


@pytest.fixture(autouse=True)
def _clear_llm_cache():
    reset_llm_cache()
    yield
    reset_llm_cache()


def test_build_llm_disables_sdk_retries():
    """SDK retries must be off so app.rag.gemini_retry owns backoff policy."""
    with patch("app.rag.llm.ChatGoogleGenerativeAI") as mock_cls:
        from app.rag.llm import _build_llm

        _build_llm(model_name="gemini-3.5-flash", temperature=0.0, google_api_key="key")
        mock_cls.assert_called_once_with(
            model="gemini-3.5-flash",
            google_api_key="key",
            temperature=0.0,
            max_retries=1,
        )


def test_get_llm_uses_settings_model_and_temperature(monkeypatch: pytest.MonkeyPatch):
    """Factory must pass config-driven model name, temperature, and API key."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("GEMINI_TEMPERATURE", "0.3")

    test_settings = Settings(_env_file=None)  # type: ignore[call-arg]

    with patch("app.rag.llm.settings", test_settings):
        with patch("app.rag.llm._build_llm") as mock_build:
            mock_build.return_value = MagicMock()
            get_llm()

    mock_build.assert_called_once_with(
        model_name="gemini-2.5-pro",
        temperature=0.3,
        google_api_key="test-google-api-key",
    )


def test_get_llm_caches_per_model_and_temperature():
    """Repeated calls with the same resolved config must reuse the cached client."""
    with patch("app.rag.llm._build_llm") as mock_build:
        sentinel = MagicMock()
        mock_build.return_value = sentinel

        first = get_llm("gemini-2.5-flash", 0.0)
        second = get_llm("gemini-2.5-flash", 0.0)

    assert first is second
    mock_build.assert_called_once()


@pytest.mark.asyncio
async def test_llm_ainvoke_returns_completion():
    """The client returned by get_llm must support async ainvoke."""
    mock_client = MagicMock()
    expected = AIMessage(content="ok")
    mock_client.ainvoke = AsyncMock(return_value=expected)

    with patch("app.rag.llm._build_llm", return_value=mock_client):
        llm = get_llm("gemini-2.5-flash", 0.0)
        result = await llm.ainvoke([HumanMessage(content="Reply with ok")])

    mock_client.ainvoke.assert_awaited_once()
    assert result.content == "ok"


def test_llm_invoke_returns_completion():
    """The client returned by get_llm must support sync invoke."""
    mock_client = MagicMock()
    expected = AIMessage(content="ok")
    mock_client.invoke.return_value = expected

    with patch("app.rag.llm._build_llm", return_value=mock_client):
        llm = get_llm("gemini-2.5-flash", 0.0)
        result = llm.invoke([HumanMessage(content="Reply with ok")])

    mock_client.invoke.assert_called_once()
    assert result.content == "ok"


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("GOOGLE_API_KEY", "test-google-api-key") in {"test-google-api-key", "your-gemini-api-key-here"},
    reason="No real GOOGLE_API_KEY set — manual/integration test only",
)
def test_real_gemini_completion():
    """Smoke test against a live Gemini API key (skipped in CI / without a real key)."""
    llm = get_llm()
    response = llm.invoke([HumanMessage(content="Reply with the single word: ok")])

    assert response.content
