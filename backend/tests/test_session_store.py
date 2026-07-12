"""Unit tests for app.services.session_store. See TASKS.md T28."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.services import session_store


@pytest.fixture
def isolated_session_store(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Point session_store at a fresh file-backed SQLite DB for each test."""
    db_path = tmp_path / "sessions.db"
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    test_settings = Settings(_env_file=None, sqlite_db_path=str(db_path))  # type: ignore[call-arg]

    with patch("app.services.session_store.settings", test_settings):
        session_store.reset_session_store()
        yield session_store
        session_store.reset_session_store()


def test_create_session_append_three_messages_returns_chronological_history(isolated_session_store):
    session_id = isolated_session_store.create_session()

    messages = [
        ("user", "What is the penalty for theft?"),
        ("assistant", "Theft is defined under Section 378 IPC."),
        ("user", "What if it is a repeat offense?"),
    ]
    for role, content in messages:
        isolated_session_store.append_message(session_id, role, content)

    history = isolated_session_store.get_history(session_id)

    assert history == [{"role": role, "content": content} for role, content in messages]


def test_get_history_unknown_session_returns_empty_list(isolated_session_store):
    history = isolated_session_store.get_history("00000000-0000-0000-0000-000000000000")

    assert history == []


def test_data_persists_across_process_restarts(isolated_session_store, tmp_path):
    session_id = isolated_session_store.create_session()
    isolated_session_store.append_message(session_id, "user", "First message")
    isolated_session_store.append_message(session_id, "assistant", "Second message")

    db_path = tmp_path / "sessions.db"
    assert db_path.exists()

    # Simulate a process restart: dispose the cached engine and reopen the DB.
    isolated_session_store.reset_session_store()

    history = isolated_session_store.get_history(session_id)

    assert history == [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "Second message"},
    ]


def test_append_message_raises_for_unknown_session(isolated_session_store):
    with pytest.raises(ValueError, match="Unknown session_id"):
        isolated_session_store.append_message(
            "00000000-0000-0000-0000-000000000000",
            "user",
            "Hello",
        )


def test_ensure_session_creates_row_for_client_supplied_id(isolated_session_store):
    client_session_id = "00000000-0000-0000-0000-000000000001"

    isolated_session_store.ensure_session(client_session_id)
    isolated_session_store.append_message(client_session_id, "user", "Hello")

    history = isolated_session_store.get_history(client_session_id)

    assert history == [{"role": "user", "content": "Hello"}]
