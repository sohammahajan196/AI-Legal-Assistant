"""
FastAPI application entrypoint.

Responsible for:
- Instantiating the FastAPI app
- Registering routers from app.api.routes
- Wiring startup/shutdown hooks (e.g. loading the FAISS/BM25 indices once at boot)

See PLAN.md Section 8 and TASKS.md T02.
"""

from fastapi import FastAPI

# TODO: from app.api.routes import chat, domains, health, sessions

app = FastAPI(title="AI Legal Assistant API")

# TODO: app.include_router(health.router)
# TODO: app.include_router(chat.router, prefix="/api/v1")
# TODO: app.include_router(sessions.router, prefix="/api/v1")
# TODO: app.include_router(domains.router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    """Placeholder startup hook (e.g. load FAISS/BM25 indices into memory).

    TODO: implement once app.rag.vectorstore / app.rag.bm25_index exist.
    """
    pass
