/**
 * Scrollable message list with empty / loading states.
 */
"use client";

import { RefObject } from "react";

import MessageBubble from "@/components/chat/MessageBubble";
import EmptyState from "@/components/chat/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import type { SourceCitation } from "@/lib/types";

export interface ChatMessageView {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: SourceCitation[];
  confidenceScore?: number;
  legalDomain?: string;
  isRefusal?: boolean;
  disclaimer?: string;
}

export interface MessageListProps {
  messages: ChatMessageView[];
  isLoadingHistory: boolean;
  isSending: boolean;
  listRef: RefObject<HTMLDivElement | null>;
  onSelectPrompt: (prompt: string) => void;
}

export default function MessageList({
  messages,
  isLoadingHistory,
  isSending,
  listRef,
  onSelectPrompt,
}: MessageListProps) {
  return (
    <div
      ref={listRef}
      className="min-h-[42rem] space-y-6 rounded-[1.75rem] border border-warm bg-surface/75 p-4 shadow-[0_24px_70px_rgb(72_52_31/8%)] backdrop-blur-sm sm:p-7 lg:p-9"
      role="log"
      aria-label="Chat messages"
    >
      {isLoadingHistory ? (
        <div className="space-y-3 py-6">
          <Skeleton className="ml-auto h-16 w-2/3" />
          <Skeleton className="h-24 w-3/4" />
          <Skeleton className="ml-auto h-12 w-1/2" />
          <p className="text-center text-sm text-ink-muted">
            Loading conversation...
          </p>
        </div>
      ) : messages.length === 0 ? (
        <EmptyState onSelectPrompt={onSelectPrompt} />
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              citations={message.citations}
              confidenceScore={message.confidenceScore}
              legalDomain={message.legalDomain}
              isRefusal={message.isRefusal}
              disclaimer={message.disclaimer}
            />
          ))}
          {isSending ? (
            <div className="flex justify-start" aria-busy="true">
              <div className="w-full max-w-[75%] space-y-2 rounded-2xl border border-warm bg-surface p-4">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
