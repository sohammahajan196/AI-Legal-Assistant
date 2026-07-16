"""Unit tests for app.rag.condense. See TASKS.md T29."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.rag.condense import condense_question
from app.rag.llm import get_llm

THEFT_HISTORY = [
    {"role": "user", "content": "What is the penalty for theft?"},
    {"role": "assistant", "content": "Theft under Section 378 IPC is punishable under Section 379."},
]


# --- no prior history: no LLM call -------------------------------------------


@pytest.mark.asyncio
async def test_no_history_returns_original_question_unchanged():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock()

    result = await condense_question(mock_llm, "What is the penalty for theft?", [])

    assert result == "What is the penalty for theft?"
    mock_llm.ainvoke.assert_not_called()


# --- prior history: LLM rewrite ----------------------------------------------


@pytest.mark.asyncio
async def test_history_present_rewrites_followup_into_standalone_question():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="What is the penalty for a repeat offense of theft under Section 378 IPC?"
        )
    )

    result = await condense_question(mock_llm, "What if it's a repeat offense?", THEFT_HISTORY)

    mock_llm.ainvoke.assert_awaited_once()
    assert "theft" in result.lower()
    assert "repeat offense" in result.lower()


@pytest.mark.asyncio
async def test_prompt_sent_to_llm_includes_history_and_followup_question():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="rewritten question"))

    await condense_question(mock_llm, "What if it's a repeat offense?", THEFT_HISTORY)

    sent_messages = mock_llm.ainvoke.await_args.args[0]
    assert isinstance(sent_messages, list)
    assert isinstance(sent_messages[0], SystemMessage)
    assert isinstance(sent_messages[1], HumanMessage)

    human_content = sent_messages[1].content
    assert "What is the penalty for theft?" in human_content
    assert "Theft under Section 378 IPC" in human_content
    assert "What if it's a repeat offense?" in human_content


@pytest.mark.asyncio
async def test_result_is_stripped_of_surrounding_whitespace():
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="  What if it's a repeat offense of theft?  \n"))

    result = await condense_question(mock_llm, "What if it's a repeat offense?", THEFT_HISTORY)

    assert result == "What if it's a repeat offense of theft?"


@pytest.mark.asyncio
async def test_list_content_blocks_from_gemini_are_normalized_to_text():
    """Gemini 3.x may return content as a list of blocks, not a bare string."""
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content=[
                {"type": "text", "text": "What is the penalty for a "},
                {"type": "text", "text": "repeat offense of theft?"},
            ]
        )
    )

    result = await condense_question(mock_llm, "What if it's a repeat offense?", THEFT_HISTORY)

    assert result == "What is the penalty for a repeat offense of theft?"


# --- function is async and awaitable -----------------------------------------


def test_condense_question_is_a_coroutine_function():
    import inspect

    assert inspect.iscoroutinefunction(condense_question)


# --- real-call smoke test -----------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("GOOGLE_API_KEY", "test-google-api-key") in {"test-google-api-key", "your-gemini-api-key-here"},
    reason="No real GOOGLE_API_KEY set — manual/integration test only",
)
@pytest.mark.asyncio
async def test_real_condense_rewrites_followup_mentioning_theft_and_repeat_offense():
    """Smoke test against a live Gemini API key (skipped in CI / without a real key)."""
    llm = get_llm()

    result = await condense_question(llm, "What if it's a repeat offense?", THEFT_HISTORY)

    assert "theft" in result.lower()
    assert "repeat offense" in result.lower() or "repeat" in result.lower()
