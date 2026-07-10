/**
 * Persistent legal disclaimer banner + consent checkbox controlling
 * consent_to_log. See PLAN.md Section 12 and TASKS.md T45.
 */
export interface DisclaimerBannerProps {
  consentToLog: boolean;
  onConsentChange: (consent: boolean) => void;
}

export default function DisclaimerBanner(props: DisclaimerBannerProps) {
  // TODO: implement banner text ("not a substitute for licensed legal
  // counsel") + consent checkbox.
  return null;
}
