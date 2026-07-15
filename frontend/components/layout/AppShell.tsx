/**
 * App shell — wider canvas with a fixed viewport fade at the bottom edge.
 */
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children: React.ReactNode;
  className?: string;
}

export default function AppShell({ children, className }: AppShellProps) {
  return (
    <>
      <div
        className={cn(
          "relative mx-auto min-h-screen w-full max-w-[92rem] px-3 py-3 sm:px-5 sm:py-4 lg:px-6 xl:px-8",
          className
        )}
      >
        {children}
      </div>
      {/* Fixed to the viewport, not page content — soft fade at screen bottom. */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-40 h-24 bg-gradient-to-t from-[var(--bg-shell)] via-[color-mix(in_srgb,var(--bg-shell)_72%,transparent)] to-transparent sm:h-28"
      />
    </>
  );
}
