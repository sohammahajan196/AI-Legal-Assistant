/**
 * Main chat page for the AI Legal Assistant UI.
 * See PLAN.md Section 12 and TASKS.md T43.
 */
import ChatWindow from "@/components/ChatWindow";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-parchment">
      <ChatWindow />
    </main>
  );
}
