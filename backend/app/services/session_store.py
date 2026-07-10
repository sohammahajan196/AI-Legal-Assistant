"""
SQLite-backed session/message store for multi-turn conversation history.

See PLAN.md Section 8 and TASKS.md T28.
"""


def create_session() -> str:
    """Create a new session and return its id.

    TODO: implement using SQLAlchemy against
    `app.core.config.settings.sqlite_db_path`, with a `sessions` table.
    """
    raise NotImplementedError


def append_message(session_id: str, role: str, content: str) -> None:
    """Append a message to a session's history (`messages` table).

    TODO: implement.
    """
    raise NotImplementedError


def get_history(session_id: str) -> list[dict]:
    """Return the ordered message history for a session.

    Must return an empty list (not raise) for an unknown `session_id`.

    TODO: implement.
    """
    raise NotImplementedError
