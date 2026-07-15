/**
 * Mobile/tablet collapsible sources list below an assistant message.
 */
"use client";

import { useId, useState } from "react";
import { ChevronDown } from "lucide-react";

import CitationCard from "@/components/CitationCard";
import { cn } from "@/lib/utils";
import type { SourceCitation } from "@/lib/types";

export interface SourcesAccordionProps {
  citations: SourceCitation[];
  defaultOpen?: boolean;
}

export default function SourcesAccordion({
  citations,
  defaultOpen = false,
}: SourcesAccordionProps) {
  const [open, setOpen] = useState(defaultOpen);
  const panelId = useId();

  if (citations.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 xl:hidden" data-testid="sources-accordion">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-controls={panelId}
        className="flex min-h-10 w-full items-center justify-between rounded-lg border border-[var(--border-cream)] bg-surface px-3 py-2 text-sm font-medium text-ink-cream transition hover:bg-surface-soft"
      >
        <span>Sources ({citations.length})</span>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-ink-cream-muted transition-transform",
            open && "rotate-180"
          )}
          aria-hidden="true"
        />
      </button>
      {open ? (
        <div id={panelId} className="mt-3 space-y-3 animate-fade-up">
          {citations.map((citation, index) => (
            <CitationCard
              key={`${citation.document}-${citation.section}-${index}`}
              document={citation.document}
              section={citation.section}
              excerpt={citation.excerpt}
              retrievalScore={citation.retrieval_score}
              actYear={citation.act_year}
              domain={citation.domain}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
