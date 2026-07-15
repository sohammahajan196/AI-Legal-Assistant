/**
 * Color-coded confidence indicator with meter bar.
 * Labels: Well grounded / Partially grounded / Insufficient grounding.
 * See PLAN.md Section 7 and TASKS.md T44.
 */
import {
  formatConfidenceScore,
  getConfidenceLevel,
} from "@/lib/confidence";
import { cn } from "@/lib/utils";

export interface ConfidenceBadgeProps {
  confidenceScore: number;
  showMeter?: boolean;
}

const LEVEL_STYLES = {
  high: "ring-1",
  mid: "ring-1",
  low: "ring-1",
} as const;

const LEVEL_LABELS = {
  high: "Well grounded",
  mid: "Partially grounded",
  low: "Insufficient grounding",
} as const;

/** Aria labels keep "High/Moderate/Low confidence" for test + a11y continuity. */
const ARIA_LEVEL_LABELS = {
  high: "High confidence",
  mid: "Moderate confidence",
  low: "Low confidence",
} as const;

const LEVEL_COLORS = {
  high: {
    bg: "var(--confidence-high-bg)",
    fg: "var(--confidence-high-fg)",
    ring: "var(--confidence-high-fg)",
  },
  mid: {
    bg: "var(--confidence-mid-bg)",
    fg: "var(--confidence-mid-fg)",
    ring: "var(--confidence-mid-fg)",
  },
  low: {
    bg: "var(--confidence-low-bg)",
    fg: "var(--confidence-low-fg)",
    ring: "var(--confidence-low-fg)",
  },
} as const;

export default function ConfidenceBadge({
  confidenceScore,
  showMeter = true,
}: ConfidenceBadgeProps) {
  const level = getConfidenceLevel(confidenceScore);
  const formattedScore = formatConfidenceScore(confidenceScore);
  const colors = LEVEL_COLORS[level];
  const percent = Math.max(0, Math.min(100, Math.round(confidenceScore * 100)));

  return (
    <div className="inline-flex flex-col gap-1.5">
      <span
        className={cn(
          "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold sm:text-sm",
          LEVEL_STYLES[level]
        )}
        style={{
          backgroundColor: colors.bg,
          color: colors.fg,
          boxShadow: `inset 0 0 0 1px ${colors.ring}33`,
        }}
        aria-label={`${ARIA_LEVEL_LABELS[level]}: ${formattedScore}`}
        data-confidence-level={level}
      >
        {LEVEL_LABELS[level]} · {formattedScore}
      </span>
      {showMeter ? (
        <div
          className="h-1 w-full min-w-[8rem] overflow-hidden rounded-full bg-[var(--border-cream)]"
          role="presentation"
          aria-hidden="true"
        >
          <div
            className="h-full rounded-full transition-[width] duration-300"
            style={{
              width: `${percent}%`,
              backgroundColor: colors.fg,
            }}
          />
        </div>
      ) : null}
    </div>
  );
}
