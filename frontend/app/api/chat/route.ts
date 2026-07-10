/**
 * Server-side proxy to the FastAPI backend's /api/v1/chat endpoint.
 *
 * The backend bearer token is read ONLY from server-side env vars here and
 * is never exposed to the client. See PLAN.md Section 12 and TASKS.md T42.
 */
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  // TODO: forward request body to `${process.env.BACKEND_API_URL}/api/v1/chat`
  // with header `Authorization: Bearer ${process.env.BACKEND_API_TOKEN}`,
  // and relay the JSON response back to the client unmodified.
  return NextResponse.json({ error: "Not implemented" }, { status: 501 });
}
