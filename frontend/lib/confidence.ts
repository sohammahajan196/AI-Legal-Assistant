/**
 * Confidence thresholds mirrored from the backend defaults in
 * app/core/config.py (CONFIDENCE_REFUSAL_THRESHOLD / CONFIDENCE_CAUTION_THRESHOLD).
 */
export const CONFIDENCE_REFUSAL_THRESHOLD = 0.4;
export const CONFIDENCE_CAUTION_THRESHOLD = 0.6;

export type ConfidenceLevel = "low" | "mid" | "high";

export function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score < CONFIDENCE_REFUSAL_THRESHOLD) {
    return "low";
  }
  if (score < CONFIDENCE_CAUTION_THRESHOLD) {
    return "mid";
  }
  return "high";
}

export function formatConfidenceScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}
