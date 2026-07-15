/**
 * Minimal site footer.
 */
export default function AppFooter() {
  return (
    <footer className="mt-8 border-t border-[var(--border-subtle)] py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-display text-[1.25rem] font-medium leading-none tracking-[-0.015em] text-ink">
            Nyāya
          </p>
          <p className="mt-1 max-w-md text-sm leading-6 text-ink-muted">
            Citation-grounded answers for Indian statute. Not a substitute for
            licensed counsel.
          </p>
        </div>
        <div className="text-xs text-ink-muted sm:text-right">
          <p>Criminal · Civil · Family · Labour · Consumer · Property</p>
          <p className="mt-1">© 2026</p>
        </div>
      </div>
    </footer>
  );
}
