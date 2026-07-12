"""Unit tests for app.services.chat_service. See TASKS.md T33."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest

from app.core.config import Settings
from app.rag.cache import reset_redis_client
from app.schemas.legal_answer import LegalAnswerResponse, LegalDomain
from app.services import chat_service
from app.services import session_store

SAMPLE_RESPONSE = LegalAnswerResponse(
    answer="Theft is punishable under Section 379 IPC.",
    confidence_score=0.85,
    legal_domain=LegalDomain.CRIMINAL,
    citations=[],
    is_refusal=False,
    disclaimer="This is not legal advice.",
)

DIFFERENT_RESPONSE = LegalAnswerResponse(
    answer="Divorce may be granted on grounds of cruelty.",
    confidence_score=0.80,
    legal_domain=LegalDomain.FAMILY,
    citations=[],
    is_refusal=False,
    disclaimer="This is not legal advice.",
)


@pytest.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    reset_redis_client()

    async def _return_fake_client():
        return client

    with patch("app.rag.cache._get_redis_client", _return_fake_client):
        yield client

    await client.aclose()
    reset_redis_client()


@pytest.fixture
def test_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    settings = Settings(_env_file=None, cache_ttl_seconds=60)  # type: ignore[call-arg]
    with patch("app.rag.cache.settings", settings):
        yield settings


@pytest.fixture
def mock_chain():
    chain_mock = AsyncMock(return_value=SAMPLE_RESPONSE)
    with patch("app.services.chat_service.run_rag_chain", chain_mock):
        yield chain_mock


@pytest.fixture
def isolated_session_store(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "sessions.db"
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    test_settings = Settings(_env_file=None, sqlite_db_path=str(db_path))  # type: ignore[call-arg]

    with patch("app.services.session_store.settings", test_settings):
        session_store.reset_session_store()
        yield session_store
        session_store.reset_session_store()


# --- cache integration -------------------------------------------------------


@pytest.mark.asyncio
async def test_repeated_identical_query_returns_cached_result_without_reinvoking_chain(
    fake_redis, test_settings, mock_chain
):
    query = "What is the punishment for theft?"

    first = await chat_service.handle_chat_request(query, session_id=None, user_type="layperson")
    second = await chat_service.handle_chat_request(query, session_id=None, user_type="layperson")

    assert first == SAMPLE_RESPONSE
    assert second == SAMPLE_RESPONSE
    mock_chain.assert_awaited_once()


@pytest.mark.asyncio
async def test_different_query_invokes_chain_again(fake_redis, test_settings, mock_chain):
    mock_chain.side_effect = [SAMPLE_RESPONSE, DIFFERENT_RESPONSE]

    first = await chat_service.handle_chat_request(
        "What is the punishment for theft?", session_id=None, user_type="layperson"
    )
    second = await chat_service.handle_chat_request(
        "What are the grounds for divorce?", session_id=None, user_type="layperson"
    )

    assert first == SAMPLE_RESPONSE
    assert second == DIFFERENT_RESPONSE
    assert mock_chain.await_count == 2


# --- session history wiring ----------------------------------------------------


@pytest.mark.asyncio
async def test_session_history_is_passed_to_chain_on_cache_miss(
    fake_redis, test_settings, mock_chain, isolated_session_store
):
    session_id = isolated_session_store.create_session()
    isolated_session_store.append_message(session_id, "user", "What is theft?")
    isolated_session_store.append_message(session_id, "assistant", "Theft is under Section 379 IPC.")

    await chat_service.handle_chat_request(
        "What if it is a repeat offense?",
        session_id=session_id,
        user_type="layperson",
    )

    mock_chain.assert_awaited_once()
    _, kwargs = mock_chain.await_args
    assert kwargs["history"] == [
        {"role": "user", "content": "What is theft?"},
        {"role": "assistant", "content": "Theft is under Section 379 IPC."},
    ]


@pytest.mark.asyncio
async def test_cache_hit_still_persists_turn_to_session(
    fake_redis, test_settings, mock_chain, isolated_session_store
):
    session_id = isolated_session_store.create_session()
    query = "What is the punishment for theft?"

    await chat_service.handle_chat_request(query, session_id=session_id, user_type="layperson")
    await chat_service.handle_chat_request(query, session_id=session_id, user_type="layperson")

    history = isolated_session_store.get_history(session_id)
    assert len(history) == 4  # two user + two assistant turns
    assert history[-2]["content"] == query
    assert history[-1]["content"] == SAMPLE_RESPONSE.answer
    mock_chain.assert_awaited_once()


@pytest.mark.asyncio
async def test_client_supplied_session_id_is_created_on_first_turn(
    fake_redis, test_settings, mock_chain, isolated_session_store
):
    client_session_id = "00000000-0000-0000-0000-000000000099"

    await chat_service.handle_chat_request(
        "What is theft?",
        session_id=client_session_id,
        user_type="layperson",
    )

    history = isolated_session_store.get_history(client_session_id)
    assert history == [
        {"role": "user", "content": "What is theft?"},
        {"role": "assistant", "content": SAMPLE_RESPONSE.answer},
    ]


# --- API layer must use chat_service only --------------------------------------


def test_api_chat_route_does_not_import_run_rag_chain_directly():
    """Acceptance criterion: chat_service is the single entrypoint; the API
    route module must delegate to it, not call app.rag.chain directly."""
    import inspect

    import app.api.routes.chat as chat_route

    source = inspect.getsource(chat_route)
    assert "run_rag_chain" not in source
    assert "chat_service" in source
