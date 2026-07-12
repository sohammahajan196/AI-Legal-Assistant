/**
 * Client-side session id persistence for multi-turn chat history.
 * See PLAN.md Section 12 and TASKS.md T47.
 */

const SESSION_ID_STORAGE_KEY = "ai-legal-assistant.session-id";

export function getStoredSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(SESSION_ID_STORAGE_KEY);
}

export function getOrCreateSessionId(): string {
  const existing = getStoredSessionId();
  if (existing) {
    return existing;
  }

  const sessionId = crypto.randomUUID();
  window.localStorage.setItem(SESSION_ID_STORAGE_KEY, sessionId);
  return sessionId;
}

/** Test helper to reset persisted session state. */
export function clearStoredSessionId(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(SESSION_ID_STORAGE_KEY);
  }
}
