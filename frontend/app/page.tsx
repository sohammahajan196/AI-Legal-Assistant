/**
 * Main chat page shell for the AI Legal Assistant UI.
 *
 * T41: default landing page with Tailwind styles visibly applied.
 * T43+ will replace this placeholder with the full <ChatWindow />.
 */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
          AI Legal Assistant
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          Indian law, explained with citations
        </h1>
        <p className="mt-4 text-base leading-relaxed text-slate-600">
          This Next.js 15 App Router frontend is scaffolded with TypeScript
          and Tailwind CSS. The chat UI and backend proxy routes will be wired
          in upcoming tasks.
        </p>
        <div className="mt-6 inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
          Tailwind CSS is active
        </div>
      </div>
    </main>
  );
}
