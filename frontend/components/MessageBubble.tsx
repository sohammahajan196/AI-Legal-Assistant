/**
 * Renders a single user or assistant chat message.
 * See TASKS.md T43/T47.
 */
import CitationCard from "./CitationCard";
import ConfidenceBadge from "./ConfidenceBadge";
import type { SourceCitation } from "@/lib/types";

export interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  citations?: SourceCitation[];
  confidenceScore?: number;
  disclaimer?: string;
}

export default function MessageBubble({
  role,
  content,
  citations = [],
  confidenceScore,
  disclaimer,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed sm:max-w-[75%] sm:text-base ${
          isUser
            ? "bg-indigo-600 text-white"
            : "border border-slate-200 bg-white text-slate-800 shadow-sm"
        }`}
      >
        <p className="whitespace-pre-wrap break-words">{content}</p>

        {!isUser && typeof confidenceScore === "number" ? (
          <div className="mt-3">
            <ConfidenceBadge confidenceScore={confidenceScore} />
          </div>
        ) : null}

        {!isUser && citations.length > 0 ? (
          <div className="mt-3 space-y-3">
            {citations.map((citation, index) => (
              <CitationCard
                key={`${citation.document}-${citation.section}-${index}`}
                document={citation.document}
                section={citation.section}
                excerpt={citation.excerpt}
                retrievalScore={citation.retrieval_score}
              />
            ))}
          </div>
        ) : null}

        {!isUser && disclaimer ? (
          <p className="mt-3 border-t border-slate-200 pt-3 text-xs leading-relaxed text-slate-600">
            {disclaimer}
          </p>
        ) : null}
      </div>
    </div>
  );
}
