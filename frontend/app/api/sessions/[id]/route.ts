/**
 * Server-side proxy to the FastAPI backend's session history endpoint.
 *
 * See PLAN.md Section 12 and TASKS.md T47.
 */
import { NextRequest, NextResponse } from "next/server";

const SENSITIVE_RESPONSE_HEADERS = new Set([
  "authorization",
  "set-cookie",
  "www-authenticate",
  "proxy-authenticate",
]);

function backendSessionsHistoryUrl(sessionId: string): string | null {
  const baseUrl = process.env.BACKEND_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    return null;
  }
  return `${baseUrl}/api/v1/sessions/${sessionId}/history`;
}

function backendBearerToken(): string | null {
  const token = process.env.BACKEND_API_TOKEN?.trim();
  return token || null;
}

function sanitizeResponseHeaders(headers: Headers): Headers {
  const sanitized = new Headers();
  headers.forEach((value, key) => {
    if (!SENSITIVE_RESPONSE_HEADERS.has(key.toLowerCase())) {
      sanitized.set(key, value);
    }
  });
  return sanitized;
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const historyUrl = backendSessionsHistoryUrl(id);
  const backendToken = backendBearerToken();

  if (!historyUrl || !backendToken) {
    return NextResponse.json(
      { error: "Backend proxy is not configured" },
      { status: 503 }
    );
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(historyUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${backendToken}`,
      },
    });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 });
  }

  return new NextResponse(await backendResponse.text(), {
    status: backendResponse.status,
    headers: sanitizeResponseHeaders(backendResponse.headers),
  });
}
