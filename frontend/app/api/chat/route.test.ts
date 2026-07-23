/**
 * Unit tests for the /api/chat server-side proxy. See TASKS.md T42.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";

import { POST } from "./route";

const BACKEND_URL = "http://backend.test";
const SERVER_TOKEN = "server-side-secret-token";
const CLIENT_TOKEN = "client-supplied-token";

const SAMPLE_BACKEND_BODY = {
  answer: "Theft is punishable under Section 379 IPC.",
  confidence_score: 0.87,
  legal_domain: "criminal",
  citations: [],
  is_refusal: false,
  disclaimer: "This is not a substitute for licensed legal counsel.",
};

function createChatRequest(
  body: unknown,
  headers: Record<string, string> = {}
): NextRequest {
  return new NextRequest("http://localhost:3000/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: JSON.stringify(body),
  });
}

describe("POST /api/chat proxy", () => {
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

  it("forwards the request body and relays the backend JSON response", async () => {
    const requestBody = {
      query: "What is theft?",
      user_type: "layperson",
      consent_to_log: true,
    };
    const backendJson = JSON.stringify(SAMPLE_BACKEND_BODY);

    fetchMock.mockResolvedValueOnce(
      new Response(backendJson, {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const response = await POST(createChatRequest(requestBody));
    const responseText = await response.text();

    expect(response.status).toBe(200);
    expect(responseText).toBe(backendJson);
    expect(JSON.parse(responseText)).toEqual(SAMPLE_BACKEND_BODY);

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BACKEND_URL}/api/v1/chat`);
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify(requestBody));
    expect(init.headers).toMatchObject({
      "Content-Type": "application/json",
      Authorization: `Bearer ${SERVER_TOKEN}`,
    });
  });

  it("uses the server env token even when the client sends Authorization", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(SAMPLE_BACKEND_BODY), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await POST(
      createChatRequest(
        { query: "What is theft?", user_type: "layperson" },
        { Authorization: `Bearer ${CLIENT_TOKEN}` }
      )
    );

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.headers).toMatchObject({
      Authorization: `Bearer ${SERVER_TOKEN}`,
    });
    expect(init.headers).not.toMatchObject({
      Authorization: `Bearer ${CLIENT_TOKEN}`,
    });
  });

  it("does not expose the backend token in the browser response", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(SAMPLE_BACKEND_BODY), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${SERVER_TOKEN}`,
        },
      })
    );

    const response = await POST(
      createChatRequest({ query: "What is theft?", user_type: "layperson" })
    );
    const responseText = await response.text();

    expect(response.headers.get("authorization")).toBeNull();
    expect(responseText).not.toContain(SERVER_TOKEN);
    expect(JSON.parse(responseText)).toEqual(SAMPLE_BACKEND_BODY);
  });

  it("strips Content-Encoding/Length so decompressed body matches headers", async () => {
    const backendJson = JSON.stringify(SAMPLE_BACKEND_BODY);

    fetchMock.mockResolvedValueOnce(
      new Response(backendJson, {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          // Simulates Render/CDN gzip that Node fetch already decompressed.
          "Content-Encoding": "gzip",
          "Content-Length": "42",
          "Transfer-Encoding": "chunked",
        },
      })
    );

    const response = await POST(
      createChatRequest({ query: "What is theft?", user_type: "layperson" })
    );
    const responseText = await response.text();

    expect(response.status).toBe(200);
    expect(response.headers.get("content-encoding")).toBeNull();
    expect(response.headers.get("content-length")).toBeNull();
    expect(response.headers.get("transfer-encoding")).toBeNull();
    expect(response.headers.get("content-type")).toBe("application/json");
    expect(JSON.parse(responseText)).toEqual(SAMPLE_BACKEND_BODY);
  });
});
