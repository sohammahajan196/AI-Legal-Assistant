/**
 * Empty conversation state with example prompt chips.
 */
"use client";

import { EXAMPLE_PROMPTS, getDomainLabel } from "@/lib/domain";
import { Button } from "@/components/ui/button";
import ScrollReveal from "@/components/motion/ScrollReveal";

export interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export default function EmptyState({ onSelectPrompt }: EmptyStateProps) {
  return (
    <div
      className="flex min-h-[42rem] flex-col justify-center px-3 py-16 sm:px-8 sm:py-20"
      data-testid="empty-state"
    >
      <ScrollReveal>
        <p className="font-mono text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-burgundy">
          Begin with a legal question
        </p>
        <h2 className="font-display mt-4 max-w-3xl text-[clamp(2.8rem,6vw,5.5rem)] font-medium leading-[0.92] tracking-[-0.035em] text-ink">
          What would you like
          <span className="block italic text-burgundy">to understand?</span>
        </h2>
        <p className="mt-6 max-w-xl text-sm leading-7 text-ink-muted sm:text-base">
          Write in your own words, or begin with a question below. Each
          response separates explanation from evidence so you can inspect the
          statute yourself.
        </p>
      </ScrollReveal>

      <div className="mt-12 grid w-full gap-3 sm:grid-cols-2">
        {EXAMPLE_PROMPTS.map((item, index) => (
          <ScrollReveal
            key={item.prompt}
            delay={(index % 3) * 70}
          >
            <Button
              type="button"
              variant="outline"
              className="group h-full min-h-[7.5rem] w-full whitespace-normal border-warm bg-[#fffaf2]/75 px-5 py-5 text-left text-sm font-normal text-ink shadow-none transition duration-300 hover:-translate-y-1 hover:border-brass hover:bg-surface hover:shadow-[0_18px_40px_rgb(72_52_31/9%)]"
              onClick={() => onSelectPrompt(item.prompt)}
            >
              <span className="flex h-full flex-col justify-between gap-5">
                <span className="font-mono text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-brass">
                  {`0${index + 1}`} · {getDomainLabel(item.domain)}
                </span>
                <span className="font-display text-xl leading-snug transition-colors group-hover:text-burgundy sm:text-[1.35rem]">
                  {item.prompt}
                </span>
              </span>
            </Button>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
