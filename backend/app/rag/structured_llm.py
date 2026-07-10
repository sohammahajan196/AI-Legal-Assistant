"""
Structured-output LLM call with bounded retry-with-repair on validation failure.

See PLAN.md Sections 5-6 and TASKS.md T23.
"""

from typing import TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


async def generate_structured_answer(llm, prompt, schema: type[SchemaT], max_retries: int = 2) -> SchemaT:
    """Invoke `llm.with_structured_output(schema, method="json_schema")` and
    retry with the validation error appended to the prompt on failure.

    TODO: implement the bounded retry-with-repair loop described in
    backend.mdc; raise a well-defined exception (not a bare exception) once
    `max_retries` is exceeded.
    """
    raise NotImplementedError
