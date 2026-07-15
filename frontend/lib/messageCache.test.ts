/**
 * Unit tests for messageCache helpers.
 */
import { beforeEach, describe, expect, it } from "vitest";

import {
  cacheAssistantMeta,
  getCachedAssistantMeta,
} from "./messageCache";

describe("messageCache", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("stores and retrieves assistant metadata by content", () => {
    const content = "Theft is defined under Section 378 IPC.";
    cacheAssistantMeta(content, {
      citations: [
        {
          document: "Indian Penal Code",
          section: "378",
          domain: "criminal",
          excerpt: "Whoever…",
          retrieval_score: 0.9,
        },
      ],
      confidenceScore: 0.88,
      legalDomain: "criminal",
      isRefusal: false,
      disclaimer: "Not legal advice.",
    });

    const cached = getCachedAssistantMeta(content);
    expect(cached).not.toBeNull();
    expect(cached?.confidenceScore).toBe(0.88);
    expect(cached?.legalDomain).toBe("criminal");
    expect(cached?.citations).toHaveLength(1);
  });

  it("returns null for unknown content", () => {
    expect(getCachedAssistantMeta("never cached")).toBeNull();
  });
});
