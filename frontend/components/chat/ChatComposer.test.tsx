import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ChatComposer from "./ChatComposer";

describe("ChatComposer", () => {
  it("stays in document flow instead of sticking over messages", () => {
    render(
      <ChatComposer value="" onChange={vi.fn()} onSubmit={vi.fn()} />
    );

    const form = screen.getByRole("form", {
      name: "Legal question composer",
    });
    expect(form).not.toHaveClass("sticky");
    expect(form).not.toHaveClass("fixed");
    expect(form).not.toHaveClass("bottom-4");
    expect(form).not.toHaveClass("z-20");
  });

  it("submits a non-empty question with Enter", () => {
    const onSubmit = vi.fn();
    render(
      <ChatComposer
        value="What is anticipatory bail?"
        onChange={vi.fn()}
        onSubmit={onSubmit}
      />
    );

    fireEvent.keyDown(screen.getByLabelText("Your message"), {
      key: "Enter",
      shiftKey: false,
    });

    expect(onSubmit).toHaveBeenCalledOnce();
  });

  it("keeps Shift + Enter available for a newline", () => {
    const onSubmit = vi.fn();
    render(
      <ChatComposer
        value="First line"
        onChange={vi.fn()}
        onSubmit={onSubmit}
      />
    );

    fireEvent.keyDown(screen.getByLabelText("Your message"), {
      key: "Enter",
      shiftKey: true,
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});
