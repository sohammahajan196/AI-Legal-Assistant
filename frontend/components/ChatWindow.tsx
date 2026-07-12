/**
 * Top-level chat container composing the message list and input.
 * See TASKS.md T43/T45.
 */
"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import DisclaimerBanner, {
  DEFAULT_CONSENT_TO_LOG,
} from "./DisclaimerBanner";
import MessageBubble from "./MessageBubble";
import {
  buildChatRequestPayload,
  type ChatApiRequestBody,
} from "@/lib/chatPayload";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [consentToLog, setConsentToLog] = useState(DEFAULT_CONSENT_TO_LOG);
  const [lastOutgoingPayload, setLastOutgoingPayload] =
    useState<ChatApiRequestBody | null>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const trimmedInput = input.trim();
  const canSend = trimmedInput.length > 0;

  useEffect(() => {
    const list = messageListRef.current;
    if (!list) {
      return;
    }
    list.scrollTop = list.scrollHeight;
  }, [messages]);

  function appendUserMessage() {
    if (!canSend) {
      return;
    }

    const outgoingPayload = buildChatRequestPayload({
      query: trimmedInput,
      userType: "layperson",
      consentToLog,
    });
    setLastOutgoingPayload(outgoingPayload);

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmedInput,
      },
    ]);
    setInput("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    appendUserMessage();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      appendUserMessage();
    }
  }

  return (
    <div className="mx-auto flex h-[100dvh] w-full max-w-4xl flex-col px-3 py-4 sm:px-6 sm:py-6">
      <DisclaimerBanner
        consentToLog={consentToLog}
        onConsentChange={setConsentToLog}
      />

      <header className="mb-4 mt-4 shrink-0 border-b border-slate-200 pb-4">
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">
          AI Legal Assistant
        </p>
        <h1 className="mt-1 text-xl font-bold text-slate-900 sm:text-2xl">
          Ask a legal question
        </h1>
        <p className="mt-1 text-sm text-slate-600 sm:text-base">
          Messages are stored locally for now. Backend responses arrive in a
          later task.
        </p>
      </header>

      <div
        ref={messageListRef}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 sm:p-6"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 ? (
          <p className="text-center text-sm text-slate-500 sm:text-base">
            Type a question below to start the conversation.
          </p>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-4 shrink-0 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4"
      >
        <label htmlFor="chat-input" className="sr-only">
          Your message
        </label>
        <textarea
          id="chat-input"
          rows={2}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about Indian law..."
          className="w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none ring-indigo-500 placeholder:text-slate-400 focus:ring-2 sm:text-base"
        />
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            disabled={!canSend}
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300 sm:text-base"
          >
            Send
          </button>
        </div>
      </form>

      {lastOutgoingPayload ? (
        <output
          aria-hidden="true"
          data-testid="last-outgoing-payload"
          className="hidden"
        >
          {JSON.stringify(lastOutgoingPayload)}
        </output>
      ) : null}
    </div>
  );
}
