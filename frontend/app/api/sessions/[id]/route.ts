/**
 * Server-side proxy to the FastAPI backend's session history endpoint.
 *
 * See PLAN.md Section 12 and TASKS.md T42.
 */
import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // TODO: forward to
  // `${process.env.BACKEND_API_URL}/api/v1/sessions/${params.id}/history`
  // with the server-side bearer token attached.
  return NextResponse.json({ error: "Not implemented" }, { status: 501 });
}
