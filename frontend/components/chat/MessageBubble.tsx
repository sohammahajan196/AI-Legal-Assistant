/**
 * Routes user vs assistant chat messages.
 */
import AssistantMessage from "@/components/chat/AssistantMessage";
import type { SourceCitation } from "@/lib/types";

export interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  citations?: SourceCitation[];
  confidenceScore?: number;
  legalDomain?: string;
  isRefusal?: boolean;
  disclaimer?: string;
}

export default function MessageBubble({
  role,
  content,
  citations = [],
  confidenceScore,
  legalDomain,
  isRefusal,
  disclaimer,
}: MessageBubbleProps) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-md bg-elevated px-4 py-3 text-sm leading-relaxed text-ink sm:max-w-[75%] sm:text-[0.95rem]">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <AssistantMessage
        content={content}
        citations={citations}
        confidenceScore={confidenceScore}
        legalDomain={legalDomain}
        isRefusal={isRefusal}
        disclaimer={disclaimer}
      />
    </div>
  );
}
