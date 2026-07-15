/**
 * Groups citations for the desktop side panel.
 */
import CitationCard from "@/components/CitationCard";
import ConfidenceBadge from "@/components/ConfidenceBadge";
import DomainBadge from "@/components/DomainBadge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import type { SourceCitation } from "@/lib/types";

export interface CitationPanelProps {
  citations: SourceCitation[];
  confidenceScore?: number;
  legalDomain?: string;
  isRefusal?: boolean;
}

export default function CitationPanel({
  citations,
  confidenceScore,
  legalDomain,
  isRefusal,
}: CitationPanelProps) {
  return (
    <aside
      className="sticky top-28 hidden h-[calc(100vh-8rem)] min-h-[34rem] w-full max-w-[400px] shrink-0 flex-col self-start overflow-hidden rounded-[1.75rem] border border-warm bg-[#171914] text-[#fff9ef] shadow-[0_24px_70px_rgb(23_25_20/18%)] xl:flex"
      aria-label="Source citations"
      data-testid="citation-panel"
    >
      <div className="shrink-0 border-b border-white/15 px-6 py-6">
        <p className="font-mono text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-[#d9bc76]">
          Evidence ledger
        </p>
        <h2 className="font-display mt-2 text-3xl font-medium text-[#fff9ef]">
          Source record
        </h2>
        {(legalDomain || typeof confidenceScore === "number" || isRefusal) && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {legalDomain ? <DomainBadge domain={legalDomain} /> : null}
            {isRefusal ? (
              <span className="rounded-md border border-[#E0C8C8] bg-[var(--confidence-low-bg)] px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide text-[var(--confidence-low-fg)]">
                Refusal
              </span>
            ) : null}
            {typeof confidenceScore === "number" ? (
              <ConfidenceBadge
                confidenceScore={confidenceScore}
                showMeter={false}
              />
            ) : null}
          </div>
        )}
      </div>

      {citations.length === 0 ? (
        <div className="flex flex-1 flex-col justify-end px-7 py-9">
          <p className="font-display text-3xl italic leading-tight text-[#d9bc76]">
            Sources will appear here after you ask a question.
          </p>
          <p className="mt-5 max-w-xs text-sm leading-6 text-[#bcb0a2]">
            Each cited section is preserved with its statutory excerpt and
            retrieval relevance.
          </p>
        </div>
      ) : (
        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-3 p-4">
            {citations.map((citation, index) => (
              <div key={`${citation.document}-${citation.section}-${index}`}>
                <CitationCard
                  document={citation.document}
                  section={citation.section}
                  excerpt={citation.excerpt}
                  retrievalScore={citation.retrieval_score}
                  actYear={citation.act_year}
                  domain={citation.domain}
                />
                {index < citations.length - 1 ? (
                  <Separator className="my-3 bg-warm" />
                ) : null}
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </aside>
  );
}
