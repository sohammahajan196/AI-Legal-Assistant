/**
 * Normalize LLM answer strings that may contain literal escape sequences
 * (e.g. "\\n" as two characters) from structured JSON output.
 */
export function normalizeAnswerText(text: string): string {
  if (!text.includes("\\")) {
    return text;
  }

  return text.replace(/\\n/g, "\n").replace(/\\t/g, "\t").replace(/\\r/g, "\r");
}
