import { Landmark } from "lucide-react";

export default function AppFooter() {
  return (
    <footer className="border-t border-ink/15 py-10 sm:py-12">
      <div className="grid gap-10 md:grid-cols-[1.2fr_0.8fr_0.8fr]">
        <div>
          <a
            href="#top"
            className="flex w-fit items-center gap-3"
            aria-label="Back to top"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-ink text-[#f5e8ca]">
              <Landmark className="h-4 w-4" aria-hidden="true" />
            </div>
            <span className="font-display text-2xl font-semibold">Nyāya</span>
          </a>
          <p className="mt-4 max-w-sm text-sm leading-6 text-ink-muted">
            Explainable legal research grounded in Indian statutory sources.
            Built for clarity, verification, and honest uncertainty.
          </p>
        </div>

        <div>
          <p className="font-mono text-[0.58rem] font-semibold uppercase tracking-[0.2em] text-burgundy">
            Explore
          </p>
          <nav className="mt-4 flex flex-col items-start gap-3" aria-label="Footer">
            <a
              href="#method"
              className="text-sm text-ink-muted transition-colors hover:text-ink"
            >
              Our method
            </a>
            <a
              href="#legal-desk"
              className="text-sm text-ink-muted transition-colors hover:text-ink"
            >
              Research desk
            </a>
          </nav>
        </div>

        <div>
          <p className="font-mono text-[0.58rem] font-semibold uppercase tracking-[0.2em] text-burgundy">
            Scope
          </p>
          <p className="mt-4 text-sm leading-6 text-ink-muted">
            Criminal, civil, family, labour, consumer, and property law.
          </p>
        </div>
      </div>

      <div className="mt-10 flex flex-col gap-3 border-t border-ink/10 pt-5 font-mono text-[0.56rem] uppercase tracking-[0.14em] text-ink-muted sm:flex-row sm:items-center sm:justify-between">
        <p>© 2026 Nyāya · Indian Legal Assistant</p>
        <p>Not legal advice · Consult licensed counsel</p>
      </div>
    </footer>
  );
}
