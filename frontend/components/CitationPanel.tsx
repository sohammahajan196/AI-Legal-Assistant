/**
 * Desktop source panel — cream panel on graphite shell.
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
      className="sticky top-6 hidden h-[calc(100vh-7rem)] min-h-[28rem] w-full max-w-[360px] shrink-0 flex-col self-start overflow-hidden rounded-2xl border border-[var(--border-cream)] bg-surface xl:flex"
      aria-label="Source citations"
      data-testid="citation-panel"
    >
      <div className="shrink-0 border-b border-[var(--border-cream)] px-5 py-4">
        <p className="text-[0.62rem] font-medium uppercase tracking-[0.14em] text-ink-cream-muted">
          Sources
        </p>
        <h2 className="mt-1 font-display text-[1.35rem] font-medium leading-none tracking-[-0.015em] text-ink-cream">
          Citations
        </h2>
        {(legalDomain || typeof confidenceScore === "number" || isRefusal) && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {legalDomain ? <DomainBadge domain={legalDomain} /> : null}
            {isRefusal ? (
              <span className="rounded-md border border-[var(--border-cream)] bg-[var(--confidence-low-bg)] px-2 py-0.5 text-[0.65rem] font-medium uppercase tracking-wide text-[var(--confidence-low-fg)]">
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
        <div className="flex flex-1 items-center px-5 py-8">
          <p className="text-sm leading-6 text-ink-cream-muted">
            Sources appear here after you ask a question.
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
                  <Separator className="my-3 bg-[var(--border-cream)]" />
                ) : null}
              </div>
            ))}
          </div>
        </ScrollArea>
      )}
    </aside>
  );
}
