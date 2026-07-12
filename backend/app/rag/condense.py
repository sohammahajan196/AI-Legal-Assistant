"""
Condense-question step: rewrites multi-turn follow-ups into standalone queries.

See PLAN.md Section 5 and TASKS.md T29.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

_CONDENSE_SYSTEM_PROMPT = (
    "Given the following conversation history and a follow-up question, "
    "rewrite the follow-up question into a standalone question that "
    "contains all the context needed to understand it without the history. "
    "Do not answer the question -- only rewrite it. Preserve the original "
    "intent and any specific legal topic mentioned in the history. Return "
    "ONLY the rewritten standalone question, with no preamble or "
    "explanation."
)

_CONDENSE_HUMAN_TEMPLATE = "Conversation history:\n{history}\n\nFollow-up question: {question}\n\nStandalone question:"

_CONDENSE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _CONDENSE_SYSTEM_PROMPT),
        ("human", _CONDENSE_HUMAN_TEMPLATE),
    ]
)


def _format_history(history: list[dict]) -> str:
    """Render prior session history as a readable transcript for the prompt."""
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)


async def condense_question(llm, question: str, history: list[dict]) -> str:
    """Rewrite `question` into a standalone query given prior session history.

    Returns the original question unchanged (no LLM call) if there is no
    prior history -- multi-turn context is meaningless with nothing to
    condense against, so skipping the LLM call avoids unnecessary latency
    and cost.
    """
    if not history:
        return question

    messages = _CONDENSE_PROMPT.format_messages(history=_format_history(history), question=question)
    response = await llm.ainvoke(messages)
    return response.content.strip()
