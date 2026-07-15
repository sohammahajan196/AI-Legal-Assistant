import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import ScrollReveal from "./ScrollReveal";

describe("ScrollReveal", () => {
  it("makes content visible when IntersectionObserver is unavailable", async () => {
    render(
      <ScrollReveal>
        <p>Evidence-led content</p>
      </ScrollReveal>
    );

    const content = screen.getByText("Evidence-led content");
    await waitFor(() =>
      expect(content.parentElement).toHaveClass("is-visible")
    );
  });

  it("applies the requested reveal direction and delay", () => {
    render(
      <ScrollReveal direction="left" delay={120}>
        <p>Animated section</p>
      </ScrollReveal>
    );

    const wrapper = screen.getByText("Animated section").parentElement;
    expect(wrapper).toHaveClass("scroll-reveal--left");
    expect(wrapper).toHaveStyle({ transitionDelay: "120ms" });
  });
});
