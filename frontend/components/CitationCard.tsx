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

export default function CitationCard(props: CitationCardProps) {
  // TODO: implement citation rendering (document, section, excerpt, score).
  return null;
}
