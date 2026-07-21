import { describe, expect, it } from "vitest";

import { normalizeAnswerText } from "@/lib/normalizeAnswerText";

describe("normalizeAnswerText", () => {
  it("passes through text without escape sequences unchanged", () => {
    expect(normalizeAnswerText("Plain answer with real\nnewlines.")).toBe(
      "Plain answer with real\nnewlines."
    );
  });

  it("converts literal backslash-n sequences to newlines", () => {
    expect(normalizeAnswerText("Line one\\n\\nLine two")).toBe("Line one\n\nLine two");
  });

  it("converts literal backslash-t sequences to tabs", () => {
    expect(normalizeAnswerText("col1\\tcol2")).toBe("col1\tcol2");
  });
});
