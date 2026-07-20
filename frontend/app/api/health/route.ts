/**
 * Frontend health probe: checks proxy env wiring and pings FastAPI
 * GET /api/v1/health (unauthenticated). See PLAN.md Section 12.
 *
 * Intended for local/dev and ops checks on :3000 — e.g.
 * `curl http://localhost:3000/api/health` — so miswired env or a down
 * backend is visible without sending a chat message.
 */
import { NextResponse } from "next/server";

export type FrontendHealthStatus = "ok" | "degraded" | "error";
export type FrontendHealthFrontend = "ok" | "misconfigured";
export type FrontendHealthBackend =
  | "ok"
  | "unavailable"
  | "unreachable"
  | "unhealthy";

export interface FrontendHealthResponse {
  status: FrontendHealthStatus;
  frontend: FrontendHealthFrontend;
  backend: FrontendHealthBackend;
  backend_token_configured: boolean;
  error?: string;
}

function backendHealthUrl(): string | null {
  const baseUrl = process.env.BACKEND_API_URL?.replace(/\/$/, "");
  if (!baseUrl) {
    return null;
  }
  return `${baseUrl}/api/v1/health`;
}

function isBackendTokenConfigured(): boolean {
  return Boolean(process.env.BACKEND_API_TOKEN?.trim());
}

function jsonHealth(
  body: FrontendHealthResponse,
  status: number
): NextResponse {
  return NextResponse.json(body, {
    status,
    headers: { "Cache-Control": "no-store" },
  });
}

export async function GET() {
  const healthUrl = backendHealthUrl();
  const backendTokenConfigured = isBackendTokenConfigured();

  if (!healthUrl) {
    return jsonHealth(
      {
        status: "error",
        frontend: "misconfigured",
        backend: "unavailable",
        backend_token_configured: backendTokenConfigured,
        error: "BACKEND_API_URL is not configured",
      },
      503
    );
  }

  let backendResponse: Response;
  try {
    backendResponse = await fetch(healthUrl, {
      method: "GET",
      cache: "no-store",
    });
  } catch {
    return jsonHealth(
      {
        status: "error",
        frontend: "ok",
        backend: "unreachable",
        backend_token_configured: backendTokenConfigured,
        error: "Backend unavailable",
      },
      502
    );
  }

  if (!backendResponse.ok) {
    return jsonHealth(
      {
        status: "error",
        frontend: "ok",
        backend: "unhealthy",
        backend_token_configured: backendTokenConfigured,
        error: `Backend health check failed (${backendResponse.status})`,
      },
      502
    );
  }

  if (!backendTokenConfigured) {
    return jsonHealth(
      {
        status: "degraded",
        frontend: "misconfigured",
        backend: "ok",
        backend_token_configured: false,
        error: "BACKEND_API_TOKEN is not configured",
      },
      503
    );
  }

  return jsonHealth(
    {
      status: "ok",
      frontend: "ok",
      backend: "ok",
      backend_token_configured: true,
    },
    200
  );
}
