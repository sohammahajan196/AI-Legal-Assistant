"""
Gemini LLM client wrapper (ChatGoogleGenerativeAI).

See PLAN.md Section 5 and TASKS.md T22.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings


def _build_llm(*, model_name: str, temperature: float, google_api_key: str) -> ChatGoogleGenerativeAI:
    """Construct a Gemini chat client from explicit configuration values."""
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=google_api_key,
        temperature=temperature,
    )


@lru_cache(maxsize=4)
def get_llm(model_name: str | None = None, temperature: float | None = None) -> ChatGoogleGenerativeAI:
    """Return a configured ``ChatGoogleGenerativeAI`` client.

    Model name and temperature are read from ``settings`` unless explicit
    overrides are supplied (useful in tests). Instances are cached per
    resolved ``(model_name, temperature)`` pair.

    Both sync (``.invoke(...)``) and async (``.ainvoke(...)``) invocation are
    supported via the returned LangChain client.
    """
    resolved_model = model_name or settings.gemini_model
    resolved_temperature = settings.gemini_temperature if temperature is None else temperature
    return _build_llm(
        model_name=resolved_model,
        temperature=resolved_temperature,
        google_api_key=settings.google_api_key.get_secret_value(),
    )


def reset_llm_cache() -> None:
    """Clear the LLM singleton cache (for tests and config reloads)."""
    get_llm.cache_clear()
