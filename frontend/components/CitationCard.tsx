/**
 * Renders a single source citation (document, section, excerpt, score).
 * See PLAN.md Section 7 and TASKS.md T44.
 */
export interface CitationCardProps {
  document: string;
  section: string;
  excerpt: string;
  retrievalScore: number;
}

function formatRetrievalScore(score: number): string {
  return `${Math.round(score * 100)}% relevance`;
}

export default function CitationCard({
  document,
  section,
  excerpt,
  retrievalScore,
}: CitationCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800 shadow-sm">
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-slate-900">{document}</p>
          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-indigo-700">
            Section {section}
          </p>
        </div>
        <p
          className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200"
          aria-label={`Retrieval relevance score ${formatRetrievalScore(retrievalScore)}`}
        >
          {formatRetrievalScore(retrievalScore)}
        </p>
      </header>
      <blockquote className="mt-3 border-l-4 border-indigo-200 pl-3 text-sm leading-relaxed text-slate-700">
        {excerpt}
      </blockquote>
    </article>
  );
}
