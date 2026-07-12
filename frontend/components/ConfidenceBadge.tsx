/**
 * Color-coded confidence indicator (green/yellow/red), using the same
 * thresholds as the backend's refusal logic.
 * See PLAN.md Section 7 and TASKS.md T44.
 */
import {
  formatConfidenceScore,
  getConfidenceLevel,
} from "@/lib/confidence";

export interface ConfidenceBadgeProps {
  confidenceScore: number;
}

const LEVEL_STYLES = {
  high: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  mid: "bg-amber-100 text-amber-900 ring-amber-200",
  low: "bg-rose-100 text-rose-800 ring-rose-200",
} as const;

const LEVEL_LABELS = {
  high: "High confidence",
  mid: "Moderate confidence",
  low: "Low confidence",
} as const;

export default function ConfidenceBadge({
  confidenceScore,
}: ConfidenceBadgeProps) {
  const level = getConfidenceLevel(confidenceScore);
  const formattedScore = formatConfidenceScore(confidenceScore);

  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 sm:text-sm ${LEVEL_STYLES[level]}`}
      aria-label={`${LEVEL_LABELS[level]}: ${formattedScore}`}
      data-confidence-level={level}
    >
      {LEVEL_LABELS[level]} · {formattedScore}
    </span>
  );
}
