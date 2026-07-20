"""
SQLite-backed session/message store for multi-turn conversation history.

See PLAN.md Section 8 and TASKS.md T28.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings
from app.core.logging import logger


class Base(DeclarativeBase):
    pass


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MessageRecord(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


@lru_cache(maxsize=1)
def _get_engine():
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return engine


def _session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=_get_engine(), expire_on_commit=False)


def reset_session_store() -> None:
    """Dispose the cached engine and clear the singleton cache (for tests)."""
    if _get_engine.cache_info().currsize:
        _get_engine().dispose()
    _get_engine.cache_clear()


def create_session() -> str:
    """Create a new session and return its id."""
    session_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    try:
        with _session_factory()() as db:
            db.add(SessionRecord(id=session_id, created_at=now))
            db.commit()
        logger.info("Database write: session created")
    except Exception as exc:
        logger.exception("Database write failed: %s", type(exc).__name__)
        raise

    return session_id


def ensure_session(session_id: str) -> None:
    """Create a session row for a client-supplied id when it does not exist yet."""
    now = datetime.now(UTC)

    try:
        with _session_factory()() as db:
            if db.get(SessionRecord, session_id) is None:
                db.add(SessionRecord(id=session_id, created_at=now))
                db.commit()
                logger.info("Database write: session ensured")
    except Exception as exc:
        logger.exception("Database write failed: %s", type(exc).__name__)
        raise


def append_message(session_id: str, role: str, content: str) -> None:
    """Append a message to a session's history (`messages` table)."""
    now = datetime.now(UTC)

    try:
        with _session_factory()() as db:
            session_exists = db.get(SessionRecord, session_id)
            if session_exists is None:
                raise ValueError(f"Unknown session_id: {session_id}")

            db.add(
                MessageRecord(
                    session_id=session_id,
                    role=role,
                    content=content,
                    created_at=now,
                )
            )
            db.commit()
        logger.info("Database write: message appended")
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Database write failed: %s", type(exc).__name__)
        raise


def get_history(session_id: str) -> list[dict]:
    """Return the ordered message history for a session.

    Returns an empty list (not raise) for an unknown `session_id`.
    """
    try:
        with _session_factory()() as db:
            session_exists = db.get(SessionRecord, session_id)
            if session_exists is None:
                return []

            rows = db.scalars(
                select(MessageRecord)
                .where(MessageRecord.session_id == session_id)
                .order_by(MessageRecord.id.asc())
            ).all()
        logger.info("Database read: session history")
    except Exception as exc:
        logger.exception("Database read failed: %s", type(exc).__name__)
        raise

    return [{"role": row.role, "content": row.content} for row in rows]
