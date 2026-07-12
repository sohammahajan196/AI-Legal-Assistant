/**
 * Unit tests for chat request payload construction. See TASKS.md T45.
 */
import { describe, expect, it } from "vitest";

import { buildChatRequestPayload } from "./chatPayload";

describe("buildChatRequestPayload", () => {
  it("includes consent_to_log=true when consent is granted", () => {
    expect(
      buildChatRequestPayload({
        query: "What is theft?",
        userType: "layperson",
        consentToLog: true,
      })
    ).toEqual({
      query: "What is theft?",
      user_type: "layperson",
      consent_to_log: true,
    });
  });

  it("includes consent_to_log=false when consent is withdrawn", () => {
    expect(
      buildChatRequestPayload({
        query: "What is theft?",
        userType: "lawyer",
        consentToLog: false,
        sessionId: "session-123",
      })
    ).toEqual({
      query: "What is theft?",
      session_id: "session-123",
      user_type: "lawyer",
      consent_to_log: false,
    });
  });
});
