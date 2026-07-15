"use client";

import { ArrowDown, BookOpenText, Quote, ShieldCheck } from "lucide-react";

import ScrollReveal from "@/components/motion/ScrollReveal";

const TRUST_MARKERS = [
  {
    number: "01",
    title: "Source-bound",
    copy: "Every legal claim maps back to retrieved statutory text.",
  },
  {
    number: "02",
    title: "Confidence shown",
    copy: "Grounding is computed from evidence—not claimed by the model.",
  },
  {
    number: "03",
    title: "Uncertainty respected",
    copy: "When reliable law is not found, the assistant refuses to guess.",
  },
];

export default function EditorialHero() {
  function moveToDesk() {
    document
      .getElementById("legal-desk")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <section className="editorial-hero relative isolate overflow-hidden rounded-[2rem] bg-ink px-5 py-14 text-[#fff9ef] sm:px-10 sm:py-16 lg:min-h-[30rem] lg:px-16 lg:py-16">
      <div className="judicial-orbit judicial-orbit--one" aria-hidden="true" />
      <div className="judicial-orbit judicial-orbit--two" aria-hidden="true" />
      <div className="absolute inset-y-0 right-[14%] hidden w-px bg-white/10 lg:block" />

      <div className="editorial-hero-grid relative z-10 grid gap-12 lg:grid-cols-[1.25fr_0.75fr] lg:gap-14">
        <div>
          <ScrollReveal>
            <div className="mb-6 flex items-center gap-3 font-mono text-[0.68rem] uppercase tracking-[0.24em] text-[#d9bc76]">
              <span className="h-px w-10 bg-[#d9bc76]" />
              Legal clarity, evidenced
            </div>
          </ScrollReveal>

          <ScrollReveal delay={90}>
            <h2 className="editorial-hero-title font-display max-w-4xl text-[clamp(3.3rem,7vw,6.8rem)] font-medium leading-[0.82] tracking-[-0.045em]">
              Understand
              <span className="block italic text-[#d9bc76]">the law.</span>
              Verify the source.
            </h2>
          </ScrollReveal>

          <ScrollReveal delay={180}>
            <div className="editorial-hero-copy mt-7 flex max-w-2xl flex-col gap-6 border-l border-[#d9bc76]/60 pl-5 sm:flex-row sm:items-end sm:justify-between sm:pl-7">
              <p className="max-w-lg text-base leading-7 text-[#e8dfd2] sm:text-lg">
                A research-led assistant for Indian statute, designed to
                explain—not invent. Ask naturally, then inspect every section
                used to form the answer.
              </p>
              <button
                type="button"
                onClick={moveToDesk}
                className="group flex h-14 w-14 shrink-0 items-center justify-center rounded-full border border-[#d9bc76]/70 text-[#d9bc76] transition duration-300 hover:-translate-y-1 hover:bg-[#d9bc76] hover:text-ink"
                aria-label="Go to legal research desk"
              >
                <ArrowDown
                  className="h-5 w-5 transition-transform group-hover:translate-y-1"
                  aria-hidden="true"
                />
              </button>
            </div>
          </ScrollReveal>
        </div>

        <ScrollReveal
          direction="right"
          delay={160}
          className="flex items-end lg:pb-4"
        >
          <div className="w-full border-t border-white/20 pt-7 lg:border-l lg:border-t-0 lg:pl-9 lg:pt-0">
            <Quote className="mb-5 h-8 w-8 text-[#d9bc76]" aria-hidden="true" />
            <blockquote className="font-display text-2xl italic leading-snug text-[#f5ecdf] sm:text-3xl">
              “Trust through traceability—not fluency alone.”
            </blockquote>
            <p className="mt-5 font-mono text-[0.65rem] uppercase tracking-[0.2em] text-[#bcb0a2]">
              Product principle · 2026
            </p>
          </div>
        </ScrollReveal>
      </div>

      <div className="editorial-hero-trust relative z-10 mt-12 grid border-t border-white/15 pt-5 sm:grid-cols-3 lg:mt-14">
        {TRUST_MARKERS.map((marker, index) => (
          <ScrollReveal
            key={marker.number}
            delay={index * 90}
            className="border-white/15 py-6 sm:border-l sm:px-7 sm:first:border-l-0 sm:first:pl-0"
          >
            <div className="flex items-start gap-4">
              <span className="font-mono text-xs text-[#d9bc76]">
                {marker.number}
              </span>
              <div>
                <h3 className="font-display text-xl font-semibold">
                  {marker.title}
                </h3>
                <p className="mt-2 max-w-xs text-sm leading-6 text-[#bcb0a2]">
                  {marker.copy}
                </p>
              </div>
            </div>
          </ScrollReveal>
        ))}
      </div>

      <BookOpenText
        className="absolute bottom-10 right-10 hidden h-6 w-6 text-white/20 sm:block"
        aria-hidden="true"
      />
      <ShieldCheck
        className="absolute right-10 top-10 h-6 w-6 text-[#d9bc76]/50"
        aria-hidden="true"
      />
    </section>
  );
}
