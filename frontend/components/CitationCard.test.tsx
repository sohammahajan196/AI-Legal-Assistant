/**
 * Unit tests for CitationCard. See TASKS.md T44.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import CitationCard from "./CitationCard";

const SAMPLE_CITATION = {
  document: "Indian Penal Code",
  section: "379",
  excerpt: "Whoever commits theft shall be punished with imprisonment...",
  retrievalScore: 0.91,
};

describe("CitationCard", () => {
  it("renders document, section, excerpt, and retrieval score legibly", () => {
    render(<CitationCard {...SAMPLE_CITATION} />);

    expect(screen.getByText("Indian Penal Code")).toBeInTheDocument();
    expect(screen.getByText("§ 379")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Whoever commits theft shall be punished with imprisonment..."
      )
    ).toBeInTheDocument();
    expect(screen.getByText("91% relevance")).toBeInTheDocument();
  });

  it("matches snapshot for sample citation data", () => {
    const { container } = render(<CitationCard {...SAMPLE_CITATION} />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
