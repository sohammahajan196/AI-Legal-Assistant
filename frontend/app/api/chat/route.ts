/**
 * Server-side proxy to the FastAPI backend's /api/v1/chat endpoint.
 *
 * The backend bearer token is read ONLY from server-side env vars here and
 * is never exposed to the client. See PLAN.md Section 12 and TASKS.md T42.
 */
import { NextRequest, NextResponse } from "next/server";

const SENSITIVE_RESPONSE_HEADERS = new Set([
  "authorization",
  "set-cookie",
  "www-authenticate",
  "proxy-authenticate",
]);

function backendChatUrl(): string | null {
  const baseUrl = process.env.BACKEND_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    return null;
  }
  return `${baseUrl}/api/v1/chat`;
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

export async function POST(request: NextRequest) {
  const chatUrl = backendChatUrl();
  const backendToken = backendBearerToken();

  if (!chatUrl || !backendToken) {
    return NextResponse.json(
      { error: "Backend proxy is not configured" },
      { status: 503 }
    );
  }

  const body = await request.text();

  let backendResponse: Response;
  try {
    backendResponse = await fetch(chatUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${backendToken}`,
      },
      body,
    });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 });
  }

  return new NextResponse(await backendResponse.text(), {
    status: backendResponse.status,
    headers: sanitizeResponseHeaders(backendResponse.headers),
  });
}
