/**
 * Minimal product header — brand + audience selector.
 */
import UserTypeSelector, {
  type UserType,
} from "@/components/UserTypeSelector";
import { Landmark } from "lucide-react";

export interface ChatHeaderProps {
  userType: UserType;
  onUserTypeChange: (value: UserType) => void;
}

export default function ChatHeader({
  userType,
  onUserTypeChange,
}: ChatHeaderProps) {
  return (
    <header
      id="top"
      className="scroll-mt-4 border-b border-[var(--border-subtle)]"
    >
      <div className="flex flex-col gap-4 py-4 sm:flex-row sm:items-center sm:justify-between">
        <a
          href="#top"
          className="flex w-fit items-center gap-3"
          aria-label="Nyāya home"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-[var(--border-subtle)] bg-elevated text-amber">
            <Landmark className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <p className="font-display text-[1.65rem] leading-none tracking-[-0.02em] text-ink">
              Nyāya
            </p>
            <p className="mt-1.5 text-[0.68rem] tracking-[0.04em] text-ink-muted">
              Indian statute assistant
            </p>
          </div>
        </a>

        <UserTypeSelector value={userType} onChange={onUserTypeChange} />
      </div>
    </header>
  );
}
