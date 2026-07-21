/**
 * ErrorAlert messaging for rate limits and upstream capacity errors.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ErrorAlert from "./ErrorAlert";

describe("ErrorAlert", () => {
  it("shows a friendly 503 message and retry button", () => {
    const onRetry = vi.fn();
    render(
      <ErrorAlert
        message="Request failed (503)"
        status={503}
        onRetry={onRetry}
      />
    );

    expect(screen.getByText("Service temporarily busy")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Our AI service is temporarily busy. Please try again in a moment."
      )
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("shows rate-limit copy for 429 responses", () => {
    render(<ErrorAlert message="Too many requests" status={429} />);

    expect(screen.getByText("Too many requests")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Rate limit reached — please wait before sending another question."
      )
    ).toBeInTheDocument();
  });
});
