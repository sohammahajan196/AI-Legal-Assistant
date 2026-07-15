/**
 * Legal domain labels and chip styles — mirrors backend DOMAIN_LABELS.
 * See PLAN.md §1 and backend/app/schemas/legal_answer.py.
 */

export const LEGAL_DOMAINS = [
  "criminal",
  "civil",
  "family",
  "labour",
  "consumer",
  "property",
  "other",
] as const;

export type LegalDomainValue = (typeof LEGAL_DOMAINS)[number];

export const DOMAIN_LABELS: Record<LegalDomainValue, string> = {
  criminal: "Criminal",
  civil: "Civil",
  family: "Family",
  labour: "Labour",
  consumer: "Consumer Protection",
  property: "Property",
  other: "Other",
};

/** Flat, muted chip styles for cream panels. */
export const DOMAIN_CHIP_STYLES: Record<LegalDomainValue, string> = {
  criminal: "bg-[#efe6e6] text-[#5e3538] border-[#e0d2d2]",
  civil: "bg-[#e7e9ee] text-[#3a4154] border-[#d0d4de]",
  family: "bg-[#ece7ec] text-[#4f3c4f] border-[#d8d0d8]",
  labour: "bg-[#e6ece8] text-[#355040] border-[#cfd8d2]",
  consumer: "bg-[#efe8da] text-[#6f5528] border-[#e0d6c0]",
  property: "bg-[#ebe7e1] text-[#4f4c46] border-[#d8d2ca]",
  other: "bg-[#e8e4de] text-[#5c5a54] border-[#d9d2c6]",
};

export function getDomainLabel(domain: string): string {
  if (domain in DOMAIN_LABELS) {
    return DOMAIN_LABELS[domain as LegalDomainValue];
  }
  return domain;
}

export function getDomainChipStyle(domain: string): string {
  if (domain in DOMAIN_CHIP_STYLES) {
    return DOMAIN_CHIP_STYLES[domain as LegalDomainValue];
  }
  return DOMAIN_CHIP_STYLES.other;
}

/** Example prompt chips for empty state — keyed by domain. */
export const EXAMPLE_PROMPTS: Array<{ domain: LegalDomainValue; prompt: string }> = [
  {
    domain: "property",
    prompt: "What can I do if my landlord won't return my security deposit?",
  },
  {
    domain: "criminal",
    prompt: "What is Section 304A of the Indian Penal Code?",
  },
  {
    domain: "labour",
    prompt: "Can my employer withhold wages for late arrival?",
  },
  {
    domain: "consumer",
    prompt: "How do I file a complaint under the Consumer Protection Act?",
  },
  {
    domain: "family",
    prompt: "What are the grounds for divorce under the Hindu Marriage Act?",
  },
  {
    domain: "civil",
    prompt: "What is the limitation period for a suit for recovery of money?",
  },
];
