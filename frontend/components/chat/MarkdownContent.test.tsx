import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import MarkdownContent from "@/components/chat/MarkdownContent";

describe("MarkdownContent", () => {
  it("renders bold markdown and paragraph breaks from literal escape sequences", () => {
    render(
      <MarkdownContent content="Intro:\\n\\n1. **Workman recovering money:** one year\\n\\n*Disclaimer: not legal advice.*" />
    );

    expect(screen.getByText("Workman recovering money:")).toBeInTheDocument();
    expect(screen.getByText("Workman recovering money:").tagName).toBe("STRONG");
    expect(screen.getByText(/Disclaimer: not legal advice\./)).toBeInTheDocument();
    expect(screen.queryByText(/\\n/)).not.toBeInTheDocument();
  });

  it("renders plain text answers unchanged", () => {
    render(<MarkdownContent content="Theft is punishable under Section 379 IPC." />);
    expect(
      screen.getByText("Theft is punishable under Section 379 IPC.")
    ).toBeInTheDocument();
  });
});
