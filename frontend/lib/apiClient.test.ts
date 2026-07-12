/**
 * Unit tests for apiClient. See TASKS.md T47.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  fetchSessionHistory,
  sendChatMessage,
} from "./apiClient";

const SAMPLE_RESPONSE = {
  answer: "Theft is punishable under Section 379 IPC.",
  confidence_score: 0.87,
  legal_domain: "criminal",
  citations: [
    {
      document: "Indian Penal Code",
      act_year: 1860,
      section: "379",
      domain: "criminal",
      excerpt: "Whoever commits theft shall be punished...",
      retrieval_score: 0.91,
    },
  ],
  is_refusal: false,
  disclaimer: "This is not a substitute for licensed legal counsel.",
};

describe("sendChatMessage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed backend JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(SAMPLE_RESPONSE), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const response = await sendChatMessage({
      query: "What is theft?",
      sessionId: "session-1",
      userType: "layperson",
      consentToLog: true,
    });

    expect(response).toEqual(SAMPLE_RESPONSE);
  });

  it("throws ApiClientError with a readable message on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "Backend unavailable" }), {
          status: 502,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    await expect(
      sendChatMessage({
        query: "What is theft?",
        userType: "layperson",
        consentToLog: true,
      })
    ).rejects.toMatchObject({
      name: "ApiClientError",
      message: "Backend unavailable",
      status: 502,
    });
  });
});

describe("fetchSessionHistory", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns ordered history messages from the sessions proxy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            session_id: "session-1",
            messages: [
              { role: "user", content: "What is theft?" },
              { role: "assistant", content: "Theft is under Section 379 IPC." },
            ],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }
        )
      )
    );

    const history = await fetchSessionHistory("session-1");

    expect(history).toEqual([
      { role: "user", content: "What is theft?" },
      { role: "assistant", content: "Theft is under Section 379 IPC." },
    ]);
  });

  it("throws ApiClientError when the sessions proxy fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "Backend unavailable" }), {
          status: 502,
        })
      )
    );

    await expect(fetchSessionHistory("session-1")).rejects.toBeInstanceOf(
      ApiClientError
    );
  });
});
