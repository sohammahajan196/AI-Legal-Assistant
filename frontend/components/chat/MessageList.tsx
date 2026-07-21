/**
 * Scrollable message list with empty / loading states.
 */
"use client";

import { RefObject } from "react";

import type { UserType } from "@/components/UserTypeSelector";
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
  userType: UserType;
  isLoadingHistory: boolean;
  isSending: boolean;
  listRef: RefObject<HTMLDivElement | null>;
  onSelectPrompt: (prompt: string) => void;
}

export default function MessageList({
  messages,
  userType,
  isLoadingHistory,
  isSending,
  listRef,
  onSelectPrompt,
}: MessageListProps) {
  return (
    <div
      ref={listRef}
      className="space-y-5 rounded-2xl border border-[var(--border-cream)] bg-surface p-4 sm:p-5"
      role="log"
      aria-label="Chat messages"
    >
      {isLoadingHistory ? (
        <div className="space-y-3 py-4">
          <Skeleton className="ml-auto h-14 w-2/3 bg-[var(--border-cream)]" />
          <Skeleton className="h-20 w-3/4 bg-[var(--border-cream)]" />
          <p className="text-center text-sm text-ink-cream-muted">
            Loading conversation...
          </p>
        </div>
      ) : messages.length === 0 ? (
        <EmptyState userType={userType} onSelectPrompt={onSelectPrompt} />
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
              <div className="w-full max-w-[75%] space-y-2 rounded-2xl border border-[var(--border-cream)] bg-surface-soft p-4">
                <Skeleton className="h-4 w-24 bg-[var(--border-cream)]" />
                <Skeleton className="h-4 w-full bg-[var(--border-cream)]" />
                <Skeleton className="h-4 w-5/6 bg-[var(--border-cream)]" />
              </div>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
