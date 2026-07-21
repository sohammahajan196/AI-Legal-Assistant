/**
 * Legal domain chip — maps domain enum to short label + muted color.
 * Colors come from `.domain-badge` rules in globals.css (cream-panel contrast).
 */
import { getDomainBadgeKey, getDomainLabel } from "@/lib/domain";
import { cn } from "@/lib/utils";

export interface DomainBadgeProps {
  domain: string;
  className?: string;
}

export default function DomainBadge({ domain, className }: DomainBadgeProps) {
  return (
    <span
      className={cn(
        "domain-badge inline-flex items-center rounded-md border px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide",
        className
      )}
      data-domain={getDomainBadgeKey(domain)}
    >
      {getDomainLabel(domain)}
    </span>
  );
}
