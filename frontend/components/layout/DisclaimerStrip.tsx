/**
 * Static legal disclaimer strip + consent checkbox.
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
      className="my-4 border-y border-[#d3c4aa] bg-[#eee4d2]/70 px-3 py-3 sm:px-4"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="flex min-w-0 flex-1 items-start gap-3">
          <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center text-burgundy">
            <Scale className="h-4 w-4" aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <p className="font-mono text-[0.56rem] font-semibold uppercase tracking-[0.18em] text-burgundy">
                Legal notice
              </p>
              <p
                className={cn(
                  "max-w-4xl text-[0.72rem] leading-5 text-ink-muted sm:text-xs",
                  !expanded && "line-clamp-2 lg:line-clamp-1"
                )}
              >
                {LEGAL_DISCLAIMER_TEXT}
              </p>
            </div>
            <button
              type="button"
              className="mt-1 font-mono text-[0.56rem] font-semibold uppercase tracking-wider text-burgundy underline-offset-2 hover:underline lg:hidden"
              onClick={() => setExpanded((v) => !v)}
              aria-expanded={expanded}
            >
              {expanded ? "Show less" : "Read more"}
            </button>
          </div>
        </div>
        <label
          htmlFor="consent-to-log"
          className="flex cursor-pointer items-center gap-2 border-t border-[#d3c4aa] pt-3 text-[0.68rem] text-ink-muted lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0"
        >
          <Checkbox
            id="consent-to-log"
            checked={consentToLog}
            onCheckedChange={(checked) => onConsentChange(checked === true)}
            data-testid="consent-checkbox"
            className="border-brass data-[state=checked]:border-burgundy data-[state=checked]:bg-burgundy"
          />
          <span className="max-w-[18rem] leading-4">
            {CONSENT_CHECKBOX_LABEL}
          </span>
        </label>
      </div>
    </aside>
  );
}
