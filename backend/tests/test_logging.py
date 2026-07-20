"""Unit tests for app.core.logging console logging. See TASKS.md T03."""

import json
import logging
import sys

import pytest

from app.core.logging import ConsoleFormatter, JsonFormatter, configure_logging, logger


def _make_record(
    message: str = "hello",
    level: int = logging.INFO,
    extra: dict | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name="app.test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


def test_console_formatter_output_is_readable():
    """Each formatted log line must be a short ``LEVEL | message`` line."""
    formatter = ConsoleFormatter()
    record = _make_record("Server started")

    assert formatter.format(record) == "INFO  | Server started"


def test_console_formatter_includes_exception_info():
    """Exception info, when present, is appended after the console line."""
    formatter = ConsoleFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        record = _make_record("failure", level=logging.ERROR)
        record.exc_info = sys.exc_info()

    formatted = formatter.format(record)

    assert formatted.startswith("ERROR | failure")
    assert "ValueError: boom" in formatted


def test_json_formatter_output_is_valid_json():
    """Each formatted log line must be a single, parseable JSON object."""
    formatter = JsonFormatter()
    record = _make_record("startup message")

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["message"] == "startup message"


def test_json_formatter_includes_timestamp_and_level():
    """Required structured fields: timestamp and level (T03 acceptance criterion)."""
    formatter = JsonFormatter()
    record = _make_record(level=logging.WARNING)

    parsed = json.loads(formatter.format(record))

    assert "timestamp" in parsed
    assert parsed["level"] == "WARNING"
    assert parsed["logger"] == "app.test"


def test_json_formatter_includes_extra_fields():
    """Fields passed via `extra=` are merged into the JSON payload."""
    formatter = JsonFormatter()
    record = _make_record(extra={"gemini_model": "gemini-2.5-flash"})

    parsed = json.loads(formatter.format(record))

    assert parsed["gemini_model"] == "gemini-2.5-flash"


def test_json_formatter_includes_exception_info():
    """Exception info, when present, is serialized as a string field."""
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        record = _make_record("failure")
        record.exc_info = sys.exc_info()

    parsed = json.loads(formatter.format(record))

    assert "ValueError: boom" in parsed["exception"]


def test_configure_logging_emits_console_lines(capsys: pytest.CaptureFixture[str]):
    """After configure_logging(), a log line is a readable console line."""
    configure_logging()

    logger.info("Server started")

    captured = capsys.readouterr()
    line = (captured.err.strip() or captured.out.strip()).splitlines()[0]

    assert line == "INFO  | Server started"
