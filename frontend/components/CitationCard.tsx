/**
 * Renders a single source citation (document, section, excerpt, score).
 * Judicial Editorial redesign with act year, domain chip, relevance bar.
 * See PLAN.md Section 7 and TASKS.md T44.
 */
import DomainBadge from "@/components/DomainBadge";

export interface CitationCardProps {
  document: string;
  section: string;
  excerpt: string;
  retrievalScore: number;
  actYear?: number | null;
  domain?: string;
}

function formatRetrievalScore(score: number): string {
  return `${Math.round(score * 100)}% relevance`;
}

export default function CitationCard({
  document,
  section,
  excerpt,
  retrievalScore,
  actYear,
  domain,
}: CitationCardProps) {
  const percent = Math.max(0, Math.min(100, Math.round(retrievalScore * 100)));
  const title =
    typeof actYear === "number" ? `${document}, ${actYear}` : document;

  return (
    <article className="rounded-xl border border-warm bg-surface p-4 text-sm text-ink shadow-sm">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-display font-semibold text-ink">{title}</p>
            {domain ? <DomainBadge domain={domain} /> : null}
          </div>
          <p className="mt-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-brass">
            {`§ ${section}`}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          <p
            className="rounded-full bg-parchment px-2.5 py-1 text-xs font-semibold text-ink-muted ring-1 ring-warm"
            aria-label={`Retrieval relevance score ${formatRetrievalScore(retrievalScore)}`}
          >
            {formatRetrievalScore(retrievalScore)}
          </p>
          <div
            className="h-1 w-16 overflow-hidden rounded-full bg-warm"
            aria-hidden="true"
          >
            <div
              className="h-full rounded-full bg-brass"
              style={{ width: `${percent}%` }}
            />
          </div>
        </div>
      </header>
      <blockquote className="mt-3 border-l-4 border-brass/50 pl-3 text-sm leading-relaxed text-ink-muted">
        {excerpt}
      </blockquote>
    </article>
  );
}
