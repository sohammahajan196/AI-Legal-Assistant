"""Unit tests for app.services.query_log. See TASKS.md T36."""

from __future__ import annotations

import hashlib
import json
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.services import query_log, session_store
from app.services.query_log import log_query


@pytest.fixture
def isolated_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Point session_store/query_log at a fresh file-backed SQLite DB."""
    db_path = tmp_path / "app.db"
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    test_settings = Settings(_env_file=None, sqlite_db_path=str(db_path))  # type: ignore[call-arg]

    with patch("app.services.session_store.settings", test_settings):
        session_store.reset_session_store()
        yield
        session_store.reset_session_store()


SAMPLE_LOG_KWARGS = {
    "token_hash": "sha256-deadbeef",
    "query": "What is the punishment for theft under IPC?",
    "retrieved_chunk_ids": ["IPC 1860, S.379", "IPC 1860, S.378"],
    "confidence_score": 0.82,
    "latency_ms": 153.4,
    "model_used": "gemini-2.5-flash",
}


def test_consent_true_stores_raw_query_text(isolated_db):
    log_query(consent_to_log=True, **SAMPLE_LOG_KWARGS)

    rows = query_log.fetch_query_logs()
    assert len(rows) == 1

    row = rows[0]
    assert row.query_text == SAMPLE_LOG_KWARGS["query"]
    assert row.query_hash == hashlib.sha256(SAMPLE_LOG_KWARGS["query"].encode()).hexdigest()


def test_consent_false_stores_hash_only_with_empty_query_text(isolated_db):
    log_query(consent_to_log=False, **SAMPLE_LOG_KWARGS)

    rows = query_log.fetch_query_logs()
    assert len(rows) == 1

    row = rows[0]
    assert row.query_text is None
    assert row.query_hash == hashlib.sha256(SAMPLE_LOG_KWARGS["query"].encode()).hexdigest()


def test_all_schema_fields_are_populated_for_sample_request(isolated_db):
    log_query(consent_to_log=True, **SAMPLE_LOG_KWARGS)

    row = query_log.fetch_query_logs()[0]

    assert row.timestamp is not None
    assert row.token_hash == SAMPLE_LOG_KWARGS["token_hash"]
    assert row.query_text == SAMPLE_LOG_KWARGS["query"]
    assert row.query_hash
    assert json.loads(row.retrieved_chunk_ids) == SAMPLE_LOG_KWARGS["retrieved_chunk_ids"]
    assert row.confidence_score == pytest.approx(SAMPLE_LOG_KWARGS["confidence_score"])
    assert row.latency_ms == pytest.approx(SAMPLE_LOG_KWARGS["latency_ms"])
    assert row.model_used == SAMPLE_LOG_KWARGS["model_used"]


def test_logging_failure_is_caught_and_does_not_raise(isolated_db, caplog):
    with patch("app.services.query_log._session_factory", side_effect=RuntimeError("DB write error")):
        with caplog.at_level("WARNING"):
            log_query(consent_to_log=True, **SAMPLE_LOG_KWARGS)

    assert any("Query log write failed" in record.message for record in caplog.records)
    assert query_log.fetch_query_logs() == []
