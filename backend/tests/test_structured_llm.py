"""Tests for app.rag.structured_llm retry-with-repair behavior. See TASKS.md T23-T24.

These cover T23's acceptance criteria directly (retry-then-succeed,
retry-exhaustion, and repair-prompt content). T24 expands edge-case coverage
(empty citations, wrong enum, malformed JSON, first-try success) separately.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.rag.structured_llm import (
    StructuredOutputGenerationError,
    generate_structured_answer,
)
from app.schemas.legal_answer import LegalDomain, LLMStructuredAnswer


def _validation_error() -> ValidationError:
    """A real ValidationError instance (e.g. from an invalid enum value)."""
    try:
        LLMStructuredAnswer(answer="x", legal_domain="not-a-real-domain")  # type: ignore[arg-type]
    except ValidationError as exc:
        return exc
    raise AssertionError("expected ValidationError")


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
