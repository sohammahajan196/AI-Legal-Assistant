/**
 * Constructs outgoing chat request bodies for the /api/chat proxy.
 * See PLAN.md Section 8 and TASKS.md T45/T46/T47.
 */
import type { ChatRequestPayload } from "@/lib/apiClient";

export interface ChatApiRequestBody {
  query: string;
  session_id?: string;
  user_type: ChatRequestPayload["userType"];
  consent_to_log: boolean;
}

export function buildChatRequestPayload(
  payload: ChatRequestPayload
): ChatApiRequestBody {
  return {
    query: payload.query,
    session_id: payload.sessionId,
    user_type: payload.userType,
    consent_to_log: payload.consentToLog,
  };
}
