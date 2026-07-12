/**
 * Unit tests for ConfidenceBadge. See TASKS.md T44.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ConfidenceBadge from "./ConfidenceBadge";
import {
  CONFIDENCE_CAUTION_THRESHOLD,
  CONFIDENCE_REFUSAL_THRESHOLD,
} from "@/lib/confidence";

describe("ConfidenceBadge", () => {
  it("renders green for scores above the caution threshold", () => {
    render(<ConfidenceBadge confidenceScore={0.87} />);

    const badge = screen.getByLabelText(/High confidence: 87%/i);
    expect(badge).toHaveAttribute("data-confidence-level", "high");
    expect(badge.className).toContain("emerald");
  });

  it("renders yellow for mid-range scores between refusal and caution thresholds", () => {
    const midScore =
      (CONFIDENCE_REFUSAL_THRESHOLD + CONFIDENCE_CAUTION_THRESHOLD) / 2;

    render(<ConfidenceBadge confidenceScore={midScore} />);

    const badge = screen.getByLabelText(/Moderate confidence/i);
    expect(badge).toHaveAttribute("data-confidence-level", "mid");
    expect(badge.className).toContain("amber");
  });

  it("renders red for scores below the refusal threshold", () => {
    render(<ConfidenceBadge confidenceScore={0.2} />);

    const badge = screen.getByLabelText(/Low confidence: 20%/i);
    expect(badge).toHaveAttribute("data-confidence-level", "low");
    expect(badge.className).toContain("rose");
  });

  it("uses backend-aligned threshold boundaries", () => {
    const { rerender } = render(
      <ConfidenceBadge confidenceScore={CONFIDENCE_CAUTION_THRESHOLD} />
    );
    expect(screen.getByLabelText("High confidence: 60%")).toHaveAttribute(
      "data-confidence-level",
      "high"
    );

    rerender(
      <ConfidenceBadge
        confidenceScore={CONFIDENCE_CAUTION_THRESHOLD - 0.01}
      />
    );
    expect(screen.getByLabelText("Moderate confidence: 59%")).toHaveAttribute(
      "data-confidence-level",
      "mid"
    );

    rerender(
      <ConfidenceBadge confidenceScore={CONFIDENCE_REFUSAL_THRESHOLD} />
    );
    expect(screen.getByLabelText("Moderate confidence: 40%")).toHaveAttribute(
      "data-confidence-level",
      "mid"
    );

    rerender(
      <ConfidenceBadge
        confidenceScore={CONFIDENCE_REFUSAL_THRESHOLD - 0.01}
      />
    );
    expect(screen.getByLabelText("Low confidence: 39%")).toHaveAttribute(
      "data-confidence-level",
      "low"
    );
  });

  it("matches snapshot for a high-confidence score", () => {
    const { container } = render(<ConfidenceBadge confidenceScore={0.87} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
