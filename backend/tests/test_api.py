"""FastAPI integration tests. See TASKS.md T40."""

# TODO: cover 401 (missing/invalid auth), 429 (rate limit), 200 happy path,
# refusal response shape, session history round-trip, and health check,
# using TestClient/httpx.AsyncClient with the RAG chain mocked and
# fakeredis instead of a real Redis instance.
