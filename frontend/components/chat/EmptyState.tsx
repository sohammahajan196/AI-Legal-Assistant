/**
 * Empty conversation state — compact guidance + simple prompt chips.
 */
"use client";

import { EXAMPLE_PROMPTS, getDomainLabel } from "@/lib/domain";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export default function EmptyState({ onSelectPrompt }: EmptyStateProps) {
  return (
    <div className="flex flex-col px-0.5 py-1" data-testid="empty-state">
      <p className="text-sm text-ink-cream-muted">
        Start with a question, or choose an example.
      </p>

      <div className="mt-3 grid w-full gap-2 sm:grid-cols-2">
        {EXAMPLE_PROMPTS.map((item) => (
          <Button
            key={item.prompt}
            type="button"
            variant="outline"
            className="h-auto min-h-0 w-full whitespace-normal border-[var(--border-cream)] bg-surface-soft px-3.5 py-2.5 text-left text-sm font-normal text-ink-cream shadow-none transition hover:border-amber/50 hover:bg-surface"
            onClick={() => onSelectPrompt(item.prompt)}
          >
            <span className="flex flex-col gap-1">
              <span className="text-[0.62rem] font-medium uppercase tracking-[0.12em] text-ink-cream-muted">
                {getDomainLabel(item.domain)}
              </span>
              <span className="leading-snug text-ink-cream">{item.prompt}</span>
            </span>
          </Button>
        ))}
      </div>
    </div>
  );
}
