"""
FastAPI application entrypoint.

Responsible for:
- Instantiating the FastAPI app
- Registering routers from app.api.routes
- Wiring startup/shutdown hooks (e.g. loading the FAISS/BM25 indices once at boot)

See PLAN.md Section 8, TASKS.md T02/T03, and general.mdc.

NOTE: importing `app.core.config` below eagerly instantiates `Settings()`, so
a missing/blank `GOOGLE_API_KEY` now makes the process fail fast at import
time with a clear pydantic validation error, rather than booting silently
and failing later inside a request (see TASKS.md T03).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes import chat, sessions
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import register_rate_limiting

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook.

    Currently just emits structured startup/shutdown log lines (T03).

    TODO: also load the FAISS/BM25 indices into memory once
    app.rag.vectorstore / app.rag.bm25_index exist.
    """
    logger.info("application_startup", extra={"gemini_model": settings.gemini_model})
    yield
    logger.info("application_shutdown")


app = FastAPI(title="AI Legal Assistant API", lifespan=lifespan)
register_rate_limiting(app, chat.limiter)

# TODO: app.include_router(health.router)
app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
# TODO: app.include_router(domains.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Liveness/boot-check route confirming the app is up (T02).

    Superseded for real health monitoring by the dedicated
    `GET /api/v1/health` route once T39 lands.
    """
    return {"name": app.title, "status": "ok"}
