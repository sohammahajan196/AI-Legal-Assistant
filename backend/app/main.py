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

# Limit tokenizer / BLAS / torch thread pools before HuggingFace or embedding
# stacks are imported (route imports pull langchain_huggingface → torch).
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"

import torch

torch.set_num_threads(1)

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api.routes import chat, domains, health, sessions
from app.core.logging import configure_logging, logger
from app.core.rate_limit import register_rate_limiting
from app.rag.exceptions import GeminiServiceUnavailableError, RetrievalIndexNotFoundError

configure_logging()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each incoming request and its final status code."""

    async def dispatch(self, request: Request, call_next) -> Response:
        logger.info("%s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception(
                "Request failed: %s %s: %s",
                request.method,
                request.url.path,
                type(exc).__name__,
            )
            raise

        if response.status_code >= 400:
            logger.error("Response sent (%s)", response.status_code)
        else:
            logger.info("Response sent (%s)", response.status_code)
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook.

    Emits console startup/shutdown log lines (T03).

    TODO: also load the FAISS/BM25 indices into memory once
    app.rag.vectorstore / app.rag.bm25_index exist.
    """
    logger.info("Server started")
    yield
    logger.info("Server stopped")


app = FastAPI(title="AI Legal Assistant API", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
register_rate_limiting(app, chat.limiter)


@app.exception_handler(RetrievalIndexNotFoundError)
async def retrieval_index_not_found_handler(
    _request: Request, exc: RetrievalIndexNotFoundError
) -> JSONResponse:
    """Map missing FAISS/BM25 artifacts to a clear 503 instead of an opaque 500."""
    logger.error("Retrieval indices missing: %s", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(GeminiServiceUnavailableError)
async def gemini_unavailable_handler(
    _request: Request, exc: GeminiServiceUnavailableError
) -> JSONResponse:
    """Map exhausted Gemini retries to a user-friendly 503."""
    logger.error(
        "Gemini service unavailable (model=%s, attempts=%s): %s",
        exc.model,
        exc.attempts,
        type(exc.last_error).__name__ if exc.last_error else "unknown",
    )
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(domains.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Liveness/boot-check route confirming the app is up (T02).

    Superseded for real health monitoring by the dedicated
    `GET /api/v1/health` route once T39 lands.
    """
    return {"name": app.title, "status": "ok"}
