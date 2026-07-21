"""Tests for app.rag.structured_llm retry-with-repair behavior. See TASKS.md T23-T24.

T23's acceptance criteria are covered directly (retry-then-succeed,
retry-exhaustion, and repair-prompt content). T24 expands edge-case coverage:
empty citations, wrong enum value, malformed JSON, and successful first-try
path. All tests are fully mocked -- no real network/LLM calls.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.rag.gemini_retry import GeminiServiceUnavailableError
from app.rag.structured_llm import (
    StructuredOutputGenerationError,
    generate_structured_answer,
)
from app.schemas.legal_answer import LegalDomain, LLMStructuredAnswer


class _FakeServerError(Exception):
    """Mimics google.genai.errors.ServerError for transient 503 tests."""

    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


def _validation_error() -> ValidationError:
    """A real ValidationError instance (e.g. from an invalid enum value)."""
    try:
        LLMStructuredAnswer(answer="x", legal_domain="not-a-real-domain")  # type: ignore[arg-type]
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")


def _malformed_json_error() -> json.JSONDecodeError:
    """A real json.JSONDecodeError, as would surface from a truncated/invalid
    JSON completion (json.JSONDecodeError is a ValueError subclass, so it's
    caught by the same repair loop as Pydantic's ValidationError)."""
    try:
        json.loads("{answer: 'missing quotes and unclosed")
    except json.JSONDecodeError as exc:
        return exc
    raise AssertionError("expected JSONDecodeError")


def _mock_llm_with_structured_llm(structured_llm: MagicMock) -> MagicMock:
    """Build a mock top-level `llm` whose `.with_structured_output(...)`
    returns the given mocked structured runnable, mirroring the real
    `llm.with_structured_output(schema, method="json_schema")` call shape."""
    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm
    return llm


@pytest.mark.asyncio
async def test_retries_and_returns_valid_result_on_second_attempt():
    """Invalid JSON/validation failure on the first call, valid result on the
    second call -> returns the valid parsed result without raising."""
    valid_result = LLMStructuredAnswer(
        answer="Theft is defined under Section 378 IPC.",
        legal_domain=LegalDomain.CRIMINAL,
        used_citation_ids=["ipc-378-0"],
    )
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[_validation_error(), valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    result = await generate_structured_answer(llm, "What is theft?", LLMStructuredAnswer)

    assert result is valid_result
    assert structured_llm.ainvoke.await_count == 2
    llm.with_structured_output.assert_called_once_with(LLMStructuredAnswer, method="json_schema")


@pytest.mark.asyncio
async def test_raises_well_defined_exception_after_exceeding_max_retries():
    """Persistent validation failure across all attempts raises
    StructuredOutputGenerationError rather than hanging or returning None."""
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=_validation_error())
    llm = _mock_llm_with_structured_llm(structured_llm)

    with pytest.raises(StructuredOutputGenerationError) as exc_info:
        await generate_structured_answer(llm, "What is theft?", LLMStructuredAnswer, max_retries=2)

    assert structured_llm.ainvoke.await_count == 3  # initial attempt + 2 retries
    assert isinstance(exc_info.value.last_error, ValidationError)


@pytest.mark.asyncio
async def test_validation_error_text_is_included_in_retry_prompt():
    """The repair prompt sent on retry must verifiably contain the previous
    validation error's text, so the LLM can self-correct."""
    error = _validation_error()
    valid_result = LLMStructuredAnswer(answer="ok", legal_domain=LegalDomain.OTHER)
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[error, valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    await generate_structured_answer(llm, "Original prompt text", LLMStructuredAnswer)

    first_call_prompt = structured_llm.ainvoke.await_args_list[0].args[0]
    retry_call_prompt = structured_llm.ainvoke.await_args_list[1].args[0]

    assert first_call_prompt == "Original prompt text"
    assert "Original prompt text" in retry_call_prompt
    assert str(error) in retry_call_prompt


@pytest.mark.asyncio
async def test_successful_first_try_makes_no_retry_call():
    """A schema-valid result on the very first attempt is returned as-is,
    with no repair/retry call made at all."""
    valid_result = LLMStructuredAnswer(
        answer="Theft is defined under Section 378 IPC.",
        legal_domain=LegalDomain.CRIMINAL,
        used_citation_ids=["ipc-378-0"],
    )
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=valid_result)
    llm = _mock_llm_with_structured_llm(structured_llm)

    result = await generate_structured_answer(llm, "What is theft?", LLMStructuredAnswer)

    assert result is valid_result
    structured_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_citations_is_a_valid_first_try_result():
    """An answer with no used_citation_ids (e.g. a refusal) is a legitimate
    schema-valid result and must not trigger a retry."""
    refusal_result = LLMStructuredAnswer(
        answer="The retrieved sources do not cover this question.",
        legal_domain=LegalDomain.OTHER,
        used_citation_ids=[],
        is_refusal=True,
    )
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=refusal_result)
    llm = _mock_llm_with_structured_llm(structured_llm)

    result = await generate_structured_answer(llm, "An out-of-scope query", LLMStructuredAnswer)

    assert result is refusal_result
    assert result.used_citation_ids == []
    structured_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_wrong_enum_value_triggers_retry_then_succeeds():
    """An invalid `legal_domain` enum value on the first attempt is a
    ValidationError that triggers exactly one repair retry, then succeeds."""
    wrong_enum_error = _validation_error()
    valid_result = LLMStructuredAnswer(answer="Corrected answer.", legal_domain=LegalDomain.FAMILY)
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[wrong_enum_error, valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    result = await generate_structured_answer(llm, "A family law question", LLMStructuredAnswer)

    assert result is valid_result
    assert structured_llm.ainvoke.await_count == 2
    retry_prompt = structured_llm.ainvoke.await_args_list[1].args[0]
    assert "legal_domain" in retry_prompt


@pytest.mark.asyncio
async def test_malformed_json_triggers_retry_then_succeeds():
    """A malformed/truncated JSON completion (JSONDecodeError) on the first
    attempt triggers exactly one repair retry, then succeeds."""
    malformed_json_error = _malformed_json_error()
    valid_result = LLMStructuredAnswer(answer="Corrected answer.", legal_domain=LegalDomain.CIVIL)
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[malformed_json_error, valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    result = await generate_structured_answer(llm, "A civil law question", LLMStructuredAnswer)

    assert result is valid_result
    assert structured_llm.ainvoke.await_count == 2
    retry_prompt = structured_llm.ainvoke.await_args_list[1].args[0]
    assert str(malformed_json_error) in retry_prompt


@pytest.mark.asyncio
async def test_repair_appends_to_chat_message_list_prompts():
    """When the prompt is a list of chat messages (not a plain string), the
    repair instruction is appended as an additional HumanMessage rather than
    silently dropped or breaking the message list shape."""
    error = _validation_error()
    valid_result = LLMStructuredAnswer(answer="ok", legal_domain=LegalDomain.LABOUR)
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[error, valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    original_messages = [
        SystemMessage(content="You are a legal assistant."),
        HumanMessage(content="What is the minimum wage?"),
    ]

    result = await generate_structured_answer(llm, original_messages, LLMStructuredAnswer)

    assert result is valid_result
    retry_prompt = structured_llm.ainvoke.await_args_list[1].args[0]
    assert isinstance(retry_prompt, list)
    assert retry_prompt[:2] == original_messages
    assert isinstance(retry_prompt[-1], HumanMessage)
    assert str(error) in retry_prompt[-1].content


@pytest.mark.asyncio
async def test_retries_transient_503_then_succeeds():
    """A Gemini 503 UNAVAILABLE on the first call is retried and recovers."""
    valid_result = LLMStructuredAnswer(answer="ok", legal_domain=LegalDomain.CRIMINAL)
    transient = _FakeServerError(
        "503 UNAVAILABLE. This model is currently experiencing high demand."
    )
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=[transient, valid_result])
    llm = _mock_llm_with_structured_llm(structured_llm)

    with patch("app.rag.gemini_retry.asyncio.sleep", new_callable=AsyncMock) as sleep:
        result = await generate_structured_answer(llm, "What is theft?", LLMStructuredAnswer)

    assert result is valid_result
    assert structured_llm.ainvoke.await_count == 2
    sleep.assert_awaited()


@pytest.mark.asyncio
async def test_exhausts_transient_503_retries_and_raises_service_unavailable():
    """Persistent 503 after transient retries raises GeminiServiceUnavailableError."""
    transient = _FakeServerError(
        "503 UNAVAILABLE. This model is currently experiencing high demand."
    )
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(side_effect=transient)
    llm = _mock_llm_with_structured_llm(structured_llm)

    with patch("app.rag.gemini_retry.asyncio.sleep", new_callable=AsyncMock):
        with patch("app.rag.gemini_retry.settings") as mock_settings:
            mock_settings.gemini_model = "gemini-3.5-flash"
            mock_settings.gemini_max_retries = 2
            mock_settings.gemini_retry_base_delay_seconds = 1.0
            mock_settings.gemini_fallback_model = ""
            with pytest.raises(GeminiServiceUnavailableError):
                await generate_structured_answer(llm, "What is theft?", LLMStructuredAnswer)

    # initial attempt + 2 transient retries
    assert structured_llm.ainvoke.await_count == 3
