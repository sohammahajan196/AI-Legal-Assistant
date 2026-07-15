/**
 * Unit tests for domains API proxy. See frontend UI plan Phase 3.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "./route";

describe("GET /api/domains", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("returns 503 when backend env is not configured", async () => {
    vi.stubEnv("BACKEND_API_URL", "");
    vi.stubEnv("BACKEND_API_TOKEN", "");

    const response = await GET();
    expect(response.status).toBe(503);
  });

  it("proxies domains from the backend with bearer auth", async () => {
    vi.stubEnv("BACKEND_API_URL", "http://backend:8000");
    vi.stubEnv("BACKEND_API_TOKEN", "test-token");

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ domains: [{ value: "criminal", label: "Criminal" }] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET();
    expect(response.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://backend:8000/api/v1/domains",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: "Bearer test-token",
        }),
      })
    );
  });
});
