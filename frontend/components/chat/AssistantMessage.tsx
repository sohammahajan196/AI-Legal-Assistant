/**
 * Assistant answer with metadata row, refusal block, disclaimer, sources.
 */
import ConfidenceBadge from "@/components/ConfidenceBadge";
import DomainBadge from "@/components/DomainBadge";
import RefusalBlock from "@/components/RefusalBlock";
import SourcesAccordion from "@/components/chat/SourcesAccordion";
import type { SourceCitation } from "@/lib/types";

export interface AssistantMessageProps {
  content: string;
  citations?: SourceCitation[];
  confidenceScore?: number;
  legalDomain?: string;
  isRefusal?: boolean;
  disclaimer?: string;
}

export default function AssistantMessage({
  content,
  citations = [],
  confidenceScore,
  legalDomain,
  isRefusal = false,
  disclaimer,
}: AssistantMessageProps) {
  const hasTrustMeta = typeof confidenceScore === "number";

  return (
    <div className="max-w-[92%] rounded-2xl rounded-tl-sm border border-warm bg-surface px-4 py-3 text-sm leading-relaxed text-ink shadow-sm animate-fade-up sm:max-w-[85%] sm:text-base">
      {hasTrustMeta || legalDomain || isRefusal ? (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {legalDomain ? <DomainBadge domain={legalDomain} /> : null}
          {isRefusal ? (
            <span className="rounded-md border border-[#E0C8C8] bg-[var(--confidence-low-bg)] px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide text-[var(--confidence-low-fg)]">
              Refusal
            </span>
          ) : null}
          {hasTrustMeta ? (
            <ConfidenceBadge confidenceScore={confidenceScore} />
          ) : null}
        </div>
      ) : (
        <p className="mb-3 text-xs italic text-ink-muted">
          Source details unavailable for earlier messages.
        </p>
      )}

      {isRefusal ? <RefusalBlock /> : null}

      <p className="whitespace-pre-wrap break-words">{content}</p>

      {citations.length > 0 ? (
        <SourcesAccordion citations={citations} defaultOpen />
      ) : null}

      {disclaimer ? (
        <p className="mt-3 border-t border-warm pt-3 text-xs italic leading-relaxed text-ink-muted">
          {disclaimer}
        </p>
      ) : null}
    </div>
  );
}
