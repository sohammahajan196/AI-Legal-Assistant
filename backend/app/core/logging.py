"""
Structured (JSON) logging configuration.

See PLAN.md Section 10 and TASKS.md T03.
"""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger for structured output.

    TODO: switch to a JSON formatter (e.g. python-json-logger) before this
    is relied on for production audit logging.
    """
    logging.basicConfig(level=level)
