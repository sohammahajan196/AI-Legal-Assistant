/**
 * Persistent legal disclaimer strip + consent checkbox.
 * Replaces DisclaimerBanner styling with Judicial Editorial treatment.
 * See PLAN.md Section 12 and TASKS.md T45.
 */
"use client";

import { useState } from "react";
import { Scale } from "lucide-react";

import { Checkbox } from "@/components/ui/checkbox";
import {
  CONSENT_CHECKBOX_LABEL,
  DEFAULT_CONSENT_TO_LOG,
  LEGAL_DISCLAIMER_TEXT,
} from "@/lib/disclaimer";
import { cn } from "@/lib/utils";

export { DEFAULT_CONSENT_TO_LOG };

export interface DisclaimerStripProps {
  consentToLog: boolean;
  onConsentChange: (consent: boolean) => void;
}

export default function DisclaimerStrip({
  consentToLog,
  onConsentChange,
}: DisclaimerStripProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <aside
      aria-label="Legal disclaimer"
      data-testid="disclaimer-banner"
      className="sticky top-3 z-30 my-3 rounded-2xl border border-[#d8c39d] bg-disclaimer/95 px-4 py-3 shadow-[0_12px_40px_rgb(72_52_31/10%)] backdrop-blur-md sm:px-5"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-[#f2d998]">
            <Scale className="h-4 w-4" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="mb-0.5 font-mono text-[0.58rem] font-semibold uppercase tracking-[0.18em] text-burgundy">
              Legal notice
            </p>
            <p
              className={cn(
                "text-xs leading-5 text-ink sm:text-sm",
                !expanded && "line-clamp-2 lg:line-clamp-1"
              )}
            >
              {LEGAL_DISCLAIMER_TEXT}
            </p>
            <button
              type="button"
              className="mt-1 font-mono text-[0.6rem] font-semibold uppercase tracking-wider text-burgundy underline-offset-2 hover:underline lg:hidden"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
            >
              {expanded ? "Show less" : "Read more"}
            </button>
          </div>
        </div>
        <label
          htmlFor="consent-to-log"
          className="flex cursor-pointer items-center gap-2.5 border-t border-[#d8c39d] pt-3 text-xs text-ink lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0"
        >
          <Checkbox
            id="consent-to-log"
            checked={consentToLog}
            onCheckedChange={(checked) => onConsentChange(checked === true)}
            data-testid="consent-checkbox"
            className="border-brass data-[state=checked]:border-burgundy data-[state=checked]:bg-burgundy"
          />
          <span className="max-w-[19rem] leading-5">{CONSENT_CHECKBOX_LABEL}</span>
        </label>
      </div>
    </aside>
  );
}
