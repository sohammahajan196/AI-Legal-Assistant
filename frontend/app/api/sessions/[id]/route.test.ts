/**
 * Unit tests for the sessions history proxy route. See TASKS.md T47.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { GET } from "./route";

const BACKEND_URL = "http://backend.test";
const SERVER_TOKEN = "server-side-secret-token";

describe("GET /api/sessions/[id] proxy", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubEnv("BACKEND_API_URL", BACKEND_URL);
    vi.stubEnv("BACKEND_API_TOKEN", SERVER_TOKEN);
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("forwards to the backend history endpoint with the server token", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          session_id: "session-1",
          messages: [{ role: "user", content: "What is theft?" }],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      )
    );

    const response = await GET(new NextRequest("http://localhost/api/sessions/session-1"), {
      params: Promise.resolve({ id: "session-1" }),
    });

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      session_id: "session-1",
      messages: [{ role: "user", content: "What is theft?" }],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      `${BACKEND_URL}/api/v1/sessions/session-1/history`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${SERVER_TOKEN}`,
        },
      }
    );
  });
});
