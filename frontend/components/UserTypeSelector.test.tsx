/**
 * Unit tests for UserTypeSelector. See TASKS.md T46.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import UserTypeSelector, { DEFAULT_USER_TYPE } from "./UserTypeSelector";

describe("UserTypeSelector", () => {
  it("defaults to layperson on first load", () => {
    expect(DEFAULT_USER_TYPE).toBe("layperson");

    render(
      <UserTypeSelector value={DEFAULT_USER_TYPE} onChange={() => {}} />
    );

    expect(screen.getByTestId("user-type-select")).toHaveValue("layperson");
  });

  it("reflects selector changes in component state immediately", () => {
    const onChange = vi.fn();

    render(<UserTypeSelector value="layperson" onChange={onChange} />);

    fireEvent.change(screen.getByTestId("user-type-select"), {
      target: { value: "lawyer" },
    });

    expect(onChange).toHaveBeenCalledWith("lawyer");
  });

  it("offers all supported user types", () => {
    render(<UserTypeSelector value="layperson" onChange={() => {}} />);

    expect(screen.getByRole("radio", { name: "Layperson" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Law student" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Lawyer" })).toBeInTheDocument();
  });
});
