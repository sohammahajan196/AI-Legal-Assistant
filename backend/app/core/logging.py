"""
Structured (JSON) logging configuration.

See PLAN.md Section 10 and TASKS.md T03.
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
    """Configure the root logger to emit structured JSON log lines.

    Replaces any existing handlers on the root logger so repeated calls
    (e.g. across test runs or `--reload` restarts) don't duplicate or
    interleave with a previously-installed plain-text handler.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
