/**
 * Routes user vs assistant chat messages.
 * See TASKS.md T43/T47.
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
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-burgundy px-4 py-3 text-sm leading-relaxed text-primary-foreground sm:max-w-[75%] sm:text-base">
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
