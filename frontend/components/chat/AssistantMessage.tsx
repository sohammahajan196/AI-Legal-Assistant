/**
 * Assistant answer with metadata, refusal, disclaimer, sources.
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
    <div className="max-w-[92%] rounded-2xl rounded-tl-md border border-[var(--border-cream)] bg-surface-soft px-4 py-3 text-sm leading-relaxed text-ink-cream animate-fade-up sm:max-w-[88%] sm:text-[0.95rem]">
      {hasTrustMeta || legalDomain || isRefusal ? (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {legalDomain ? <DomainBadge domain={legalDomain} /> : null}
          {isRefusal ? (
            <span className="rounded-md border border-[var(--border-cream)] bg-[var(--confidence-low-bg)] px-2 py-0.5 text-[0.65rem] font-medium uppercase tracking-wide text-[var(--confidence-low-fg)]">
              Refusal
            </span>
          ) : null}
          {hasTrustMeta ? (
            <ConfidenceBadge confidenceScore={confidenceScore} />
          ) : null}
        </div>
      ) : (
        <p className="mb-3 text-xs text-ink-cream-muted">
          Source details unavailable for earlier messages.
        </p>
      )}

      {isRefusal ? <RefusalBlock /> : null}

      <p className="whitespace-pre-wrap break-words">{content}</p>

      {citations.length > 0 ? (
        <SourcesAccordion citations={citations} defaultOpen />
      ) : null}

      {disclaimer ? (
        <p className="mt-3 border-t border-[var(--border-cream)] pt-3 text-xs leading-relaxed text-ink-cream-muted">
          {disclaimer}
        </p>
      ) : null}
    </div>
  );
}
