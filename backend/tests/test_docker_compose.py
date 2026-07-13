"""Sanity checks for root docker-compose.yml. See TASKS.md T53."""

from __future__ import annotations

from pathlib import Path

COMPOSE_PATH = Path(__file__).resolve().parents[2] / "docker-compose.yml"


def test_compose_declares_three_services_with_named_volumes():
    text = COMPOSE_PATH.read_text(encoding="utf-8")

    for service in ("redis:", "backend:", "frontend:"):
        assert service in text

    for volume in ("redis_data:", "faiss_index:", "sqlite_data:"):
        assert volume in text


def test_compose_wires_frontend_to_backend_and_redis_healthchecks():
    text = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "BACKEND_API_URL: http://backend:8000" in text
    assert "REDIS_URL: redis://redis:6379/0" in text
    assert "condition: service_healthy" in text
    assert "faiss_index:/app/data/faiss_index" in text
