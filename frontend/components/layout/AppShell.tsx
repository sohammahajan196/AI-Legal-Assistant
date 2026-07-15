/**
 * App shell — minimal dark graphite canvas.
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
        "relative mx-auto min-h-screen w-full max-w-6xl px-4 py-4 sm:px-6 sm:py-5 lg:px-8",
        className
      )}
    >
      {children}
    </div>
  );
}
