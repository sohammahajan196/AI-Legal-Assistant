/**
 * Chat header — Fraunces wordmark + user type selector.
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
    <header className="flex flex-col gap-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:py-5">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-full border border-ink/20 bg-ink text-[#f5e8ca] shadow-[0_8px_24px_rgb(23_25_20/12%)]">
          <Landmark className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <p className="font-display text-2xl font-semibold leading-none tracking-[-0.02em] text-ink">
            Nyāya
          </p>
          <p className="mt-1 font-mono text-[0.6rem] uppercase tracking-[0.2em] text-ink-muted">
            Indian legal intelligence
          </p>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <p className="hidden max-w-[13rem] text-right text-xs leading-5 text-ink-muted lg:block">
          Citation-grounded explanations from Indian statutory law.
        </p>
        <UserTypeSelector value={userType} onChange={onUserTypeChange} />
      </div>
    </header>
  );
}
