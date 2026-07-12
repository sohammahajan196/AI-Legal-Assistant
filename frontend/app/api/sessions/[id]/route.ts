/**
 * Server-side proxy to the FastAPI backend's session history endpoint.
 *
 * See PLAN.md Section 12 and TASKS.md T42.
 */
import { NextRequest, NextResponse } from "next/server";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  // TODO: forward to
  // `${process.env.BACKEND_API_URL}/api/v1/sessions/${id}/history`
  // with the server-side bearer token attached.
  return NextResponse.json({ error: "Not implemented", sessionId: id }, { status: 501 });
}
