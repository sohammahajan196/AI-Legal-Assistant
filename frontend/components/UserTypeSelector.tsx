/**
 * layperson / law_student / lawyer segmented control.
 * See PLAN.md §5 / TASKS.md T46.
 */
"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

export type UserType = "layperson" | "law_student" | "lawyer";

/** Default audience on first load, matching backend prompts.py. */
export const DEFAULT_USER_TYPE: UserType = "layperson";

const USER_TYPE_OPTIONS: Array<{
  value: UserType;
  label: string;
  hint: string;
}> = [
  {
    value: "layperson",
    label: "Layperson",
    hint: "Plain-language answers with clear next steps",
  },
  {
    value: "law_student",
    label: "Law student",
    hint: "Precise citations and statutory nuance",
  },
  {
    value: "lawyer",
    label: "Lawyer",
    hint: "Fast citation lookup with minimal hand-holding",
  },
];

export interface UserTypeSelectorProps {
  value: UserType;
  onChange: (value: UserType) => void;
}

export default function UserTypeSelector({
  value,
  onChange,
}: UserTypeSelectorProps) {
  return (
    <TooltipProvider delayDuration={300}>
      <div className="shrink-0">
        <p className="mb-1.5 text-[0.62rem] font-medium uppercase tracking-[0.12em] text-ink-muted">
          Audience
        </p>
        <select
          id="user-type-select"
          data-testid="user-type-select"
          value={value}
          onChange={(event) => onChange(event.target.value as UserType)}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          aria-label="Audience type (select)"
        >
          {USER_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ToggleGroup
          type="single"
          value={value}
          onValueChange={(next) => {
            if (next) {
              onChange(next as UserType);
            }
          }}
          variant="default"
          size="sm"
          className="justify-start gap-0 overflow-hidden rounded-lg border border-[var(--border-subtle)] bg-elevated p-0.5"
          aria-label="Audience type"
        >
          {USER_TYPE_OPTIONS.map((option) => {
            const isSelected = value === option.value;

            return (
            <Tooltip key={option.value}>
              <TooltipTrigger asChild>
                <ToggleGroupItem
                  value={option.value}
                  aria-label={option.label}
                  data-selected={isSelected ? "true" : "false"}
                  className="audience-option min-h-9 rounded-md border-0 px-3 text-xs sm:text-sm"
                >
                  {option.label}
                </ToggleGroupItem>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="max-w-[220px]">
                {option.hint}
              </TooltipContent>
            </Tooltip>
            );
          })}
        </ToggleGroup>
      </div>
    </TooltipProvider>
  );
}
