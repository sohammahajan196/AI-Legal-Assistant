/**
 * Integration-style tests for consent wiring in ChatWindow. See TASKS.md T45.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ChatWindow from "./ChatWindow";

describe("ChatWindow consent wiring", () => {
  it("reflects unchecked consent in the stub outgoing payload", () => {
    render(<ChatWindow />);

    fireEvent.click(screen.getByTestId("consent-checkbox"));
    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is bail?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    const payload = JSON.parse(
      screen.getByTestId("last-outgoing-payload").textContent ?? "{}"
    );

    expect(payload.consent_to_log).toBe(false);
    expect(payload.query).toBe("What is bail?");
  });

  it("keeps consent_to_log true by default in the stub outgoing payload", () => {
    render(<ChatWindow />);

    fireEvent.change(screen.getByLabelText("Your message"), {
      target: { value: "What is theft?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    const payload = JSON.parse(
      screen.getByTestId("last-outgoing-payload").textContent ?? "{}"
    );

    expect(payload.consent_to_log).toBe(true);
  });
});
