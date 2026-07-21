/**
 * Main chat page.
 * See PLAN.md Section 12 and TASKS.md T43.
 */
import ChatWindow from "@/components/ChatWindow";
import { parseAudienceParam } from "@/lib/audience";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ audience?: string | string[] }>;
}) {
  const params = await searchParams;
  const rawAudience = Array.isArray(params.audience)
    ? params.audience[0]
    : params.audience;
  const initialUserType = parseAudienceParam(rawAudience);

  return (
    <main className="min-h-screen bg-shell">
      <ChatWindow initialUserType={initialUserType} />
    </main>
  );
}
