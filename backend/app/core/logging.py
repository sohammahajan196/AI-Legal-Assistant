"""
Console logging configuration.

See PLAN.md Section 10 and TASKS.md T03. Default output is a short, readable
console line (``INFO  | message``) so operators can follow request flow in the
server terminal. ``JsonFormatter`` remains available for structured sinks.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

# Attributes present on every stdlib LogRecord that we don't want to re-emit
# verbatim (either redundant with fields we compute ourselves, or internal).
_RESERVED_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
}

APP_LOGGER_NAME = "app"

# Shared application logger — import this instead of creating per-module loggers.
logger = logging.getLogger(APP_LOGGER_NAME)


class ConsoleFormatter(logging.Formatter):
    """Renders each log record as a short, terminal-friendly line.

    Example: ``INFO  | Server started``
    """

    def format(self, record: logging.LogRecord) -> str:
        level = f"{record.levelname:<5}"
        line = f"{level} | {record.getMessage()}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


class JsonFormatter(logging.Formatter):
    """Renders each log record as a single-line JSON object.

    Always includes `timestamp` (ISO-8601, UTC), `level`, `logger`, and
    `message`. Any fields passed via `extra=` are merged in, and exception
    info (if present) is included as a `exception` string.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger to emit short console log lines.

    Replaces any existing handlers on the root logger so repeated calls
    (e.g. across test runs or `--reload` restarts) don't duplicate or
    interleave with a previously-installed handler.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(ConsoleFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    logging.getLogger(APP_LOGGER_NAME).setLevel(level)
