/**
 * Color-coded confidence indicator (green/yellow/red), using the same
 * thresholds as the backend's refusal logic.
 * See PLAN.md Section 7 and TASKS.md T44.
 */
export interface ConfidenceBadgeProps {
  confidenceScore: number;
}

export default function ConfidenceBadge(props: ConfidenceBadgeProps) {
  // TODO: implement threshold-based color coding (mirror backend
  // CONFIDENCE_REFUSAL_THRESHOLD / CONFIDENCE_CAUTION_THRESHOLD).
  return null;
}
