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

/** `data-domain` key for `.domain-badge` CSS in globals.css. */
export function getDomainBadgeKey(domain: string): LegalDomainValue | "other" {
  if (domain in DOMAIN_LABELS) {
    return domain as LegalDomainValue;
  }
  return "other";
}

export function getDomainLabel(domain: string): string {
  if (domain in DOMAIN_LABELS) {
    return DOMAIN_LABELS[domain as LegalDomainValue];
  }
  return domain;
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
