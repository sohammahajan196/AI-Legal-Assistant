/**
 * Audience (user_type) persistence via URL query param and audience-specific UI copy.
 * See PLAN.md §5 and backend/app/rag/prompts.py.
 */
import {
  DEFAULT_USER_TYPE,
  type UserType,
} from "@/components/UserTypeSelector";

/** Query param used in the URL (?audience=lawyer). */
export const AUDIENCE_QUERY_PARAM = "audience";

const VALID_USER_TYPES = new Set<UserType>([
  "layperson",
  "law_student",
  "lawyer",
]);

export function isUserType(value: string): value is UserType {
  return VALID_USER_TYPES.has(value as UserType);
}

/** Parse ?audience= from the URL; invalid or missing values fall back to layperson. */
export function parseAudienceParam(
  raw: string | null | undefined
): UserType {
  if (raw && isUserType(raw)) {
    return raw;
  }
  return DEFAULT_USER_TYPE;
}

/** Audience-specific on-page copy (backend prompts handle answer tone separately). */
export const AUDIENCE_UI_COPY: Record<
  UserType,
  { pageSubtitle: string; emptyIntro: string }
> = {
  layperson: {
    pageSubtitle:
      "Plain-language answers with citations, confidence scores, and source excerpts.",
    emptyIntro:
      "Start with a question in everyday language, or choose an example below.",
  },
  law_student: {
    pageSubtitle:
      "Statutory analysis with citations, confidence scores, and source excerpts.",
    emptyIntro:
      "Ask about a section, concept, or doctrine — or pick an example below.",
  },
  lawyer: {
    pageSubtitle:
      "Concise citation-backed answers with confidence scores and source excerpts.",
    emptyIntro:
      "Query a provision or issue directly, or choose an example below.",
  },
};

/** Update the audience query param in the URL without reloading the page. */
export function navigateWithAudience(userType: UserType): void {
  const url = new URL(window.location.href);
  url.searchParams.set(AUDIENCE_QUERY_PARAM, userType);
  window.history.replaceState(null, "", url.toString());
}
