/**
 * Unit tests for DisclaimerBanner. See TASKS.md T45.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DisclaimerBanner, {
  DEFAULT_CONSENT_TO_LOG,
} from "./DisclaimerBanner";
import { LEGAL_DISCLAIMER_TEXT } from "@/lib/disclaimer";

describe("DisclaimerBanner", () => {
  it("renders the legal disclaimer text persistently", () => {
    render(
      <DisclaimerBanner consentToLog={DEFAULT_CONSENT_TO_LOG} onConsentChange={() => {}} />
    );

    expect(screen.getByTestId("disclaimer-banner")).toBeInTheDocument();
    expect(screen.getByText(LEGAL_DISCLAIMER_TEXT)).toBeInTheDocument();
  });

  it("defaults consent checkbox to the documented backend-aligned value", () => {
    expect(DEFAULT_CONSENT_TO_LOG).toBe(true);

    render(
      <DisclaimerBanner consentToLog={DEFAULT_CONSENT_TO_LOG} onConsentChange={() => {}} />
    );

    expect(screen.getByTestId("consent-checkbox")).toBeChecked();
  });

  it("notifies the parent when consent is toggled", () => {
    const onConsentChange = vi.fn();

    render(
      <DisclaimerBanner consentToLog={true} onConsentChange={onConsentChange} />
    );

    fireEvent.click(screen.getByTestId("consent-checkbox"));

    expect(onConsentChange).toHaveBeenCalledWith(false);
  });

  it("matches snapshot", () => {
    const { container } = render(
      <DisclaimerBanner consentToLog={true} onConsentChange={() => {}} />
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
