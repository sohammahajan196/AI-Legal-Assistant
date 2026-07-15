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

/** Muted chip color classes per domain — warm editorial palette. */
export const DOMAIN_CHIP_STYLES: Record<LegalDomainValue, string> = {
  criminal: "bg-[#F0E4E4] text-[#6E2F2F] border-[#E0C8C8]",
  civil: "bg-[#E8EAF0] text-[#3A4560] border-[#C8CFE0]",
  family: "bg-[#F0E8F0] text-[#5C3A5C] border-[#D8C8D8]",
  labour: "bg-[#E8F0EB] text-[#3D5C45] border-[#C8D8CE]",
  consumer: "bg-[#F5EBD8] text-[#8A5A18] border-[#E5D5B0]",
  property: "bg-[#EDE8E0] text-[#5C5348] border-[#D8D0C0]",
  other: "bg-muted text-muted-foreground border-border",
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
