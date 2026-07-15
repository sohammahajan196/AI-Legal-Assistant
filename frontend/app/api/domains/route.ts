/**
 * Server-side proxy to FastAPI GET /api/v1/domains.
 * Bearer token stays server-side only.
 */
import { NextResponse } from "next/server";

const SENSITIVE_RESPONSE_HEADERS = new Set([
  "authorization",
  "set-cookie",
  "www-authenticate",
  "proxy-authenticate",
]);

function backendDomainsUrl(): string | null {
  const baseUrl = process.env.BACKEND_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    return null;
  }
  return `${baseUrl}/api/v1/domains`;
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

export async function GET() {
  const domainsUrl = backendDomainsUrl();
  const backendToken = backendBearerToken();

  if (!domainsUrl || !backendToken) {
    return NextResponse.json(
      { error: "Backend proxy is not configured" },
      { status: 503 }
    );
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(domainsUrl, {
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
