"""
Structured-output LLM call with bounded retry-with-repair on validation failure.

See PLAN.md Sections 5-6 and TASKS.md T23.
"""

from __future__ import annotations

from typing import TypeVar

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)

REPAIR_INSTRUCTION_TEMPLATE = (
    "Your previous response failed schema validation with the following "
    "error. Correct your answer so it strictly matches the required JSON "
    "schema and try again.\n\nValidation error:\n{error}"
)


class StructuredOutputGenerationError(Exception):
    """Raised when the LLM fails to produce schema-valid structured output
    within the bounded retry budget.

    Carries the last validation/parsing error for diagnostics and logging,
    per backend.mdc's "never silently swallow validation failures" rule.
    """

    def __init__(self, message: str, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.last_error = last_error


def _append_repair_instruction(prompt: str | list[BaseMessage], error: Exception) -> str | list[BaseMessage]:
    """Return a new prompt with the validation error appended, preserving
    the original prompt's shape (plain string or chat message list)."""
    repair_text = REPAIR_INSTRUCTION_TEMPLATE.format(error=error)
    if isinstance(prompt, str):
        return f"{prompt}\n\n{repair_text}"
    if isinstance(prompt, list):
        return [*prompt, HumanMessage(content=repair_text)]
    raise TypeError(f"Unsupported prompt type for repair: {type(prompt)!r}")


async def generate_structured_answer(
    llm, prompt: str | list[BaseMessage], schema: type[SchemaT], max_retries: int = 2
) -> SchemaT:
    """Invoke `llm.with_structured_output(schema, method="json_schema")` and
    retry with the validation error appended to the prompt on failure.

    Bounded to `max_retries` re-invocations (per backend.mdc); on final
    exhaustion, raises `StructuredOutputGenerationError` rather than hanging
    or silently returning `None`. Catches `ValueError` (the base class of
    both Pydantic's `ValidationError` and `json.JSONDecodeError`) so both
    schema-violation and malformed-JSON failures trigger the repair loop.
    """
    structured_llm = llm.with_structured_output(schema, method="json_schema")

    current_prompt = prompt
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await structured_llm.ainvoke(current_prompt)
        except ValueError as exc:
            last_error = exc
            if attempt < max_retries:
                current_prompt = _append_repair_instruction(current_prompt, exc)

    raise StructuredOutputGenerationError(
        f"Failed to generate a valid {schema.__name__} after {max_retries} retries",
        last_error=last_error,
    )
