/**
 * App shell — balanced side gutters with a soft white viewport frost.
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
          "relative mx-auto min-h-screen w-full max-w-7xl px-6 py-4 sm:px-10 sm:py-5 lg:px-14 xl:px-16",
          className
        )}
      >
        {children}
      </div>
      {/* Fixed to the viewport — faint white frost, not a dark fade. */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-40 h-28 sm:h-32"
        style={{
          background:
            "linear-gradient(to top, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.03) 45%, rgba(255,255,255,0) 100%)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          maskImage:
            "linear-gradient(to top, black 0%, black 35%, transparent 100%)",
          WebkitMaskImage:
            "linear-gradient(to top, black 0%, black 35%, transparent 100%)",
        }}
      />
    </>
  );
}
