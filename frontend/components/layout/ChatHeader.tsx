/**
 * Chat header — Fraunces wordmark + user type selector.
 */
import UserTypeSelector, {
  type UserType,
} from "@/components/UserTypeSelector";
import { ArrowDownRight, Landmark } from "lucide-react";

export interface ChatHeaderProps {
  userType: UserType;
  onUserTypeChange: (value: UserType) => void;
}

export default function ChatHeader({
  userType,
  onUserTypeChange,
}: ChatHeaderProps) {
  return (
    <header id="top" className="scroll-mt-4 border-b border-ink/15">
      <div className="flex min-h-[5.5rem] flex-col gap-5 py-4 sm:flex-row sm:items-center sm:justify-between">
        <a
          href="#top"
          className="group flex w-fit items-center gap-3"
          aria-label="Nyāya home"
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-full border border-ink/20 bg-ink text-[#f5e8ca] shadow-[0_8px_24px_rgb(23_25_20/12%)] transition-transform duration-300 group-hover:-translate-y-0.5">
            <Landmark className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <p className="font-display text-2xl font-semibold leading-none tracking-[-0.02em] text-ink">
              Nyāya
            </p>
            <p className="mt-1 font-mono text-[0.58rem] uppercase tracking-[0.2em] text-ink-muted">
              Indian legal intelligence
            </p>
          </div>
        </a>

        <nav
          className="hidden items-center gap-7 md:flex"
          aria-label="Primary navigation"
        >
          <a
            href="#method"
            className="font-mono text-[0.62rem] font-medium uppercase tracking-[0.16em] text-ink-muted transition-colors hover:text-burgundy"
          >
            Method
          </a>
          <a
            href="#legal-desk"
            className="font-mono text-[0.62rem] font-medium uppercase tracking-[0.16em] text-ink-muted transition-colors hover:text-burgundy"
          >
            Research desk
          </a>
          <a
            href="#legal-desk"
            className="group inline-flex items-center gap-2 rounded-full border border-ink/20 px-4 py-2.5 font-mono text-[0.62rem] font-semibold uppercase tracking-[0.14em] text-ink transition hover:border-burgundy hover:bg-burgundy hover:text-white"
          >
            Ask Nyāya
            <ArrowDownRight
              className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:translate-y-0.5"
              aria-hidden="true"
            />
          </a>
        </nav>

        <div className="flex items-center gap-5">
          <UserTypeSelector value={userType} onChange={onUserTypeChange} />
        </div>
      </div>
    </header>
  );
}
