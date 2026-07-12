/**
 * Thin wrapper around calls to the /api/chat and /api/sessions/* proxy
 * routes, keeping fetch/error-handling logic out of components.
 * See TASKS.md T47.
 */
import { buildChatRequestPayload } from "@/lib/chatPayload";
import type {
  HistoryMessage,
  LegalAnswerResponse,
  SessionHistoryResponse,
} from "@/lib/types";

export interface ChatRequestPayload {
  query: string;
  sessionId?: string;
  userType: "layperson" | "law_student" | "lawyer";
  consentToLog: boolean;
}

export class ApiClientError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      error?: string;
      detail?: string | { msg?: string }[];
    };
    if (typeof body.error === "string") {
      return body.error;
    }
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Fall through to the generic message below.
  }
  return `Request failed (${response.status})`;
}

export async function sendChatMessage(
  payload: ChatRequestPayload
): Promise<LegalAnswerResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildChatRequestPayload(payload)),
  });

  if (!response.ok) {
    throw new ApiClientError(await readErrorMessage(response), response.status);
  }

  return response.json() as Promise<LegalAnswerResponse>;
}

export async function fetchSessionHistory(
  sessionId: string
): Promise<HistoryMessage[]> {
  const response = await fetch(`/api/sessions/${sessionId}`);

  if (!response.ok) {
    throw new ApiClientError(await readErrorMessage(response), response.status);
  }

  const body = (await response.json()) as SessionHistoryResponse;
  return body.messages;
}
