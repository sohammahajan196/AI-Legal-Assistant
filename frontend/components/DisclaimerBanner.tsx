/**
 * Persistent legal disclaimer banner + consent checkbox controlling
 * consent_to_log. See PLAN.md Section 12 and TASKS.md T45.
 */
import {
  CONSENT_CHECKBOX_LABEL,
  DEFAULT_CONSENT_TO_LOG,
  LEGAL_DISCLAIMER_TEXT,
} from "@/lib/disclaimer";

export { DEFAULT_CONSENT_TO_LOG };

export interface DisclaimerBannerProps {
  consentToLog: boolean;
  onConsentChange: (consent: boolean) => void;
}

export default function DisclaimerBanner({
  consentToLog,
  onConsentChange,
}: DisclaimerBannerProps) {
  return (
    <aside
      role="note"
      aria-label="Legal disclaimer"
      data-testid="disclaimer-banner"
      className="sticky top-0 z-10 shrink-0 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 shadow-sm"
    >
      <p className="text-sm leading-relaxed text-amber-950 sm:text-base">
        {LEGAL_DISCLAIMER_TEXT}
      </p>
      <label className="mt-3 flex cursor-pointer items-start gap-2 text-sm text-amber-950">
        <input
          type="checkbox"
          checked={consentToLog}
          onChange={(event) => onConsentChange(event.target.checked)}
          data-testid="consent-checkbox"
          className="mt-0.5 h-4 w-4 rounded border-amber-300 text-indigo-600 focus:ring-indigo-500"
        />
        <span>{CONSENT_CHECKBOX_LABEL}</span>
      </label>
    </aside>
  );
}
