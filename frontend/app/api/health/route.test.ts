/**
 * Unit tests for GET /api/health frontend probe.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

describe("GET /api/health", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("returns 503 when BACKEND_API_URL is missing", async () => {
    vi.stubEnv("BACKEND_API_URL", "");
    vi.stubEnv("BACKEND_API_TOKEN", "test-token");

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(503);
    expect(body).toMatchObject({
      status: "error",
      frontend: "misconfigured",
      backend: "unavailable",
      backend_token_configured: true,
      error: "BACKEND_API_URL is not configured",
    });
  });

  it("returns 503 when the backend is up but BACKEND_API_TOKEN is missing", async () => {
    vi.stubEnv("BACKEND_API_URL", "http://backend:8000");
    vi.stubEnv("BACKEND_API_TOKEN", "");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(503);
    expect(body).toMatchObject({
      status: "degraded",
      frontend: "misconfigured",
      backend: "ok",
      backend_token_configured: false,
      error: "BACKEND_API_TOKEN is not configured",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://backend:8000/api/v1/health",
      expect.objectContaining({ method: "GET" })
    );
  });

  it("returns 502 when the backend cannot be reached", async () => {
    vi.stubEnv("BACKEND_API_URL", "http://backend:8000");
    vi.stubEnv("BACKEND_API_TOKEN", "test-token");
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("ECONNREFUSED")));

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(502);
    expect(body).toMatchObject({
      status: "error",
      frontend: "ok",
      backend: "unreachable",
      error: "Backend unavailable",
    });
  });

  it("returns 200 when env is wired and backend health is ok", async () => {
    vi.stubEnv("BACKEND_API_URL", "http://backend:8000");
    vi.stubEnv("BACKEND_API_TOKEN", "test-token");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET();
    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body).toEqual({
      status: "ok",
      frontend: "ok",
      backend: "ok",
      backend_token_configured: true,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://backend:8000/api/v1/health",
      expect.objectContaining({ method: "GET" })
    );
  });
});
