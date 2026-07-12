/**
 * Unit tests for shared confidence threshold helpers. See TASKS.md T44.
 */
import { describe, expect, it } from "vitest";

import {
  CONFIDENCE_CAUTION_THRESHOLD,
  CONFIDENCE_REFUSAL_THRESHOLD,
  getConfidenceLevel,
} from "./confidence";

describe("confidence thresholds", () => {
  it("mirrors backend default refusal and caution thresholds", () => {
    expect(CONFIDENCE_REFUSAL_THRESHOLD).toBe(0.4);
    expect(CONFIDENCE_CAUTION_THRESHOLD).toBe(0.6);
  });

  it("classifies scores into low, mid, and high bands", () => {
    expect(getConfidenceLevel(0.2)).toBe("low");
    expect(getConfidenceLevel(0.5)).toBe("mid");
    expect(getConfidenceLevel(0.8)).toBe("high");
  });
});
