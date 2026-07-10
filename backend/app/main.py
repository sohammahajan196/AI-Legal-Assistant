"""
FastAPI application entrypoint.

Responsible for:
- Instantiating the FastAPI app
- Registering routers from app.api.routes
- Wiring startup/shutdown hooks (e.g. loading the FAISS/BM25 indices once at boot)

See PLAN.md Section 8 and TASKS.md T02.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

# TODO: from app.api.routes import chat, domains, health, sessions


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Placeholder startup/shutdown hook (e.g. load FAISS/BM25 indices into memory).

    TODO: implement once app.rag.vectorstore / app.rag.bm25_index exist.
    """
    yield


app = FastAPI(title="AI Legal Assistant API", lifespan=lifespan)

# TODO: app.include_router(health.router)
# TODO: app.include_router(chat.router, prefix="/api/v1")
# TODO: app.include_router(sessions.router, prefix="/api/v1")
# TODO: app.include_router(domains.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Liveness/boot-check route confirming the app is up (T02).

    Superseded for real health monitoring by the dedicated
    `GET /api/v1/health` route once T39 lands.
    """
    return {"name": app.title, "status": "ok"}
