/**
 * App shell — full-height parchment atmosphere for the chat UI.
 */
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children: React.ReactNode;
  className?: string;
}

export default function AppShell({ children, className }: AppShellProps) {
  return (
    <div
      className={cn(
        "relative mx-auto min-h-screen w-full max-w-[96rem] px-3 py-3 sm:px-6 sm:py-5 lg:px-8",
        className
      )}
    >
      {children}
    </div>
  );
}
