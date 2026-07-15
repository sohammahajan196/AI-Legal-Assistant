/**
 * Static legal disclaimer strip + consent checkbox.
 * Non-sticky; sits directly below the header.
 * See PLAN.md Section 12 and TASKS.md T45.
 */
"use client";

import { useState } from "react";

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
      className="my-3 border-b border-[var(--border-subtle)] bg-disclaimer/80 px-1 py-3"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <p className="text-[0.62rem] font-medium uppercase tracking-[0.14em] text-ink-muted">
              Notice
            </p>
            <p
              className={cn(
                "max-w-3xl text-xs leading-5 text-ink-muted",
                !expanded && "line-clamp-2 lg:line-clamp-1"
              )}
            >
              {LEGAL_DISCLAIMER_TEXT}
            </p>
          </div>
          <button
            type="button"
            className="mt-1 text-[0.62rem] font-medium text-amber underline-offset-2 hover:underline lg:hidden"
            onClick={() => setExpanded((v) => !v)}
            aria-expanded={expanded}
          >
            {expanded ? "Show less" : "Read more"}
          </button>
        </div>
        <label
          htmlFor="consent-to-log"
          className="flex cursor-pointer items-center gap-2 border-t border-[var(--border-subtle)] pt-3 text-xs text-ink-muted lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0"
        >
          <Checkbox
            id="consent-to-log"
            checked={consentToLog}
            onCheckedChange={(checked) => onConsentChange(checked === true)}
            data-testid="consent-checkbox"
            className="border-ink-muted data-[state=checked]:border-amber data-[state=checked]:bg-amber data-[state=checked]:text-primary-foreground"
          />
          <span className="max-w-[17rem] leading-4">{CONSENT_CHECKBOX_LABEL}</span>
        </label>
      </div>
    </aside>
  );
}
