/**
 * Thin wrapper around calls to the /api/chat and /api/sessions/* proxy
 * routes, keeping fetch/error-handling logic out of components.
 * See TASKS.md T47.
 */

export interface ChatRequestPayload {
  query: string;
  sessionId?: string;
  userType: "layperson" | "law_student" | "lawyer";
  consentToLog: boolean;
}

export async function sendChatMessage(
  payload: ChatRequestPayload
): Promise<unknown> {
  // TODO: implement fetch("/api/chat", { method: "POST", ... }) with error
  // handling surfaced to the caller.
  throw new Error("Not implemented");
}
