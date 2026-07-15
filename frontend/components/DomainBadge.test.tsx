/**
 * Unit tests for DomainBadge.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import DomainBadge from "./DomainBadge";

describe("DomainBadge", () => {
  it("renders a human-readable domain label", () => {
    render(<DomainBadge domain="criminal" />);
    expect(screen.getByText("Criminal")).toBeInTheDocument();
    expect(screen.getByText("Criminal")).toHaveAttribute(
      "data-domain",
      "criminal"
    );
  });

  it("falls back gracefully for unknown domains", () => {
    render(<DomainBadge domain="admiralty" />);
    expect(screen.getByText("admiralty")).toBeInTheDocument();
  });
});
