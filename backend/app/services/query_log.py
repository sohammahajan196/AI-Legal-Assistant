"""
Consent-aware audit logging to the `query_logs` table.

See PLAN.md Section 10 and TASKS.md T36.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from app.services.session_store import Base, _get_engine, _session_factory

logger = logging.getLogger(__name__)


class QueryLogRecord(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    query_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_hash: Mapped[str] = mapped_column(String, nullable=False)
    retrieved_chunk_ids: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    model_used: Mapped[str] = mapped_column(String, nullable=False)


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()


def _ensure_query_log_table() -> None:
    """Create the ``query_logs`` table in the shared SQLite database if needed."""
    Base.metadata.create_all(_get_engine(), tables=[QueryLogRecord.__table__])


def log_query(
    token_hash: str,
    query: str,
    consent_to_log: bool,
    retrieved_chunk_ids: list[str],
    confidence_score: float,
    latency_ms: float,
    model_used: str,
) -> None:
    """Persist a query log entry.

    Stores the raw ``query`` text only if ``consent_to_log`` is True; otherwise
    only a hash is stored and ``query_text`` is left null. Must catch and
    swallow its own failures so logging never fails the parent request (see
    database.mdc).
    """
    try:
        _ensure_query_log_table()

        record = QueryLogRecord(
            timestamp=datetime.now(UTC),
            token_hash=token_hash,
            query_text=query if consent_to_log else None,
            query_hash=_hash_query(query),
            retrieved_chunk_ids=json.dumps(retrieved_chunk_ids),
            confidence_score=confidence_score,
            latency_ms=latency_ms,
            model_used=model_used,
        )

        with _session_factory()() as db:
            db.add(record)
            db.commit()
    except Exception as exc:
        logger.warning("Query log write failed, skipping: %s", exc)


def fetch_query_logs() -> list[QueryLogRecord]:
    """Return all persisted query log rows (intended for tests/diagnostics)."""
    _ensure_query_log_table()
    with _session_factory()() as db:
        return list(db.scalars(select(QueryLogRecord).order_by(QueryLogRecord.id.asc())).all())
