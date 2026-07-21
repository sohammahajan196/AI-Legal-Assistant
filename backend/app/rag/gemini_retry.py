"""
Explicit retry / fallback handling for transient Gemini API capacity errors.

The google-genai SDK performs its own retries when ``max_retries > 1`` on
``ChatGoogleGenerativeAI``. We disable that (``max_retries=1`` in
``app.rag.llm``) and control backoff, attempt limits, and optional model
fallback here instead.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

from langchain_core.messages import BaseMessage

from app.core.config import settings
from app.core.logging import logger
from app.rag.exceptions import GeminiServiceUnavailableError

def is_transient_gemini_error(exc: BaseException) -> bool:
    """True for Gemini 503 / UNAVAILABLE capacity spikes (retryable)."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status == 503:
        return True
    message = str(exc).upper()
    return "503" in message and ("UNAVAILABLE" in message or "HIGH DEMAND" in message)


def compute_backoff_delay(attempt: int, base_delay_seconds: float) -> float:
    """Exponential backoff for attempt index 0, 1, 2, … plus small jitter."""
    delay = base_delay_seconds * (2**attempt)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


async def _ainvoke_with_retries(
    llm: Any,
    prompt: str | list[BaseMessage],
    *,
    model_label: str,
    max_retries: int,
    base_delay_seconds: float,
    operation: str,
) -> Any:
    """Invoke ``llm.ainvoke`` with bounded exponential backoff on 503 errors."""
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await llm.ainvoke(prompt)
        except ValueError:
            raise
        except Exception as exc:
            if not is_transient_gemini_error(exc):
                logger.exception(
                    "LLM request failed (%s, model=%s): %s",
                    operation,
                    model_label,
                    type(exc).__name__,
                )
                raise

            last_error = exc
            if attempt >= max_retries:
                break

            delay = compute_backoff_delay(attempt, base_delay_seconds)
            logger.warning(
                "Gemini capacity error (%s); retry %s/%s on model=%s in %.2fs: %s",
                operation,
                attempt + 1,
                max_retries,
                model_label,
                delay,
                type(exc).__name__,
            )
            await asyncio.sleep(delay)

    logger.error(
        "Gemini unavailable after %s attempts (%s, model=%s); giving up",
        max_retries + 1,
        operation,
        model_label,
    )
    raise GeminiServiceUnavailableError(
        GeminiServiceUnavailableError.USER_MESSAGE,
        last_error=last_error,
        model=model_label,
        attempts=max_retries + 1,
    )


async def ainvoke_with_gemini_resilience(
    llm: Any,
    prompt: str | list[BaseMessage],
    *,
    operation: str = "llm_call",
    model_label: str | None = None,
    max_retries: int | None = None,
    base_delay_seconds: float | None = None,
    enable_fallback: bool = True,
) -> Any:
    """Call Gemini with explicit retries and optional fallback model."""
    resolved_model = model_label or settings.gemini_model
    resolved_max_retries = settings.gemini_max_retries if max_retries is None else max_retries
    resolved_base_delay = (
        settings.gemini_retry_base_delay_seconds
        if base_delay_seconds is None
        else base_delay_seconds
    )

    try:
        return await _ainvoke_with_retries(
            llm,
            prompt,
            model_label=resolved_model,
            max_retries=resolved_max_retries,
            base_delay_seconds=resolved_base_delay,
            operation=operation,
        )
    except GeminiServiceUnavailableError as primary_error:
        if not enable_fallback:
            raise

        from app.rag.llm import get_fallback_llm

        fallback_llm = get_fallback_llm()
        if fallback_llm is None:
            raise

        fallback_model = settings.gemini_fallback_model.strip()
        logger.warning(
            "Primary Gemini model %s unavailable after %s attempts; "
            "falling back to %s (%s)",
            resolved_model,
            primary_error.attempts,
            fallback_model,
            operation,
        )
        return await _ainvoke_with_retries(
            fallback_llm,
            prompt,
            model_label=fallback_model,
            max_retries=resolved_max_retries,
            base_delay_seconds=resolved_base_delay,
            operation=operation,
        )
