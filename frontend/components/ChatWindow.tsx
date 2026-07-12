/**
 * Top-level chat container composing the message list and input.
 * See TASKS.md T43/T45/T46/T47.
 */
"use client";

import {
  FormEvent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import DisclaimerBanner, {
  DEFAULT_CONSENT_TO_LOG,
} from "./DisclaimerBanner";
import MessageBubble from "./MessageBubble";
import UserTypeSelector, {
  DEFAULT_USER_TYPE,
  type UserType,
} from "./UserTypeSelector";
import {
  ApiClientError,
  fetchSessionHistory,
  sendChatMessage,
} from "@/lib/apiClient";
import { buildChatRequestPayload, type ChatApiRequestBody } from "@/lib/chatPayload";
import { getOrCreateSessionId } from "@/lib/sessionStorage";
import type { SourceCitation } from "@/lib/types";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: SourceCitation[];
  confidenceScore?: number;
  disclaimer?: string;
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [consentToLog, setConsentToLog] = useState(DEFAULT_CONSENT_TO_LOG);
  const [userType, setUserType] = useState<UserType>(DEFAULT_USER_TYPE);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastOutgoingPayload, setLastOutgoingPayload] =
    useState<ChatApiRequestBody | null>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const trimmedInput = input.trim();
  const canSend = trimmedInput.length > 0 && !isSending && !isLoadingHistory;

  const scrollToBottom = useCallback(() => {
    const list = messageListRef.current;
    if (!list) {
      return;
    }
    list.scrollTop = list.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    let cancelled = false;

    async function loadSessionHistory() {
      const activeSessionId = getOrCreateSessionId();
      if (!cancelled) {
        setSessionId(activeSessionId);
      }

      try {
        const history = await fetchSessionHistory(activeSessionId);
        if (cancelled) {
          return;
        }

        setMessages(
          history.map((message) => ({
            id: crypto.randomUUID(),
            role: message.role,
            content: message.content,
          }))
        );
      } catch (error) {
        if (!cancelled) {
          const message =
            error instanceof ApiClientError
              ? error.message
              : "Unable to load previous messages.";
          setErrorMessage(message);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingHistory(false);
        }
      }
    }

    void loadSessionHistory();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSend() {
    if (!canSend || !sessionId) {
      return;
    }

    const query = trimmedInput;
    const outgoingPayload = buildChatRequestPayload({
      query,
      sessionId,
      userType,
      consentToLog,
    });
    setLastOutgoingPayload(outgoingPayload);
    setErrorMessage(null);
    setInput("");
    setIsSending(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: query,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendChatMessage({
        query,
        sessionId,
        userType,
        consentToLog,
      });

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.answer,
          citations: response.citations,
          confidenceScore: response.confidence_score,
          disclaimer: response.disclaimer,
        },
      ]);
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : "Something went wrong while contacting the assistant.";
      setErrorMessage(message);
    } finally {
      setIsSending(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleSend();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
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
          Answers are grounded in retrieved legal sources with citations and a
          confidence score.
        </p>
        <UserTypeSelector value={userType} onChange={setUserType} />
      </header>

      {errorMessage ? (
        <div
          role="alert"
          data-testid="chat-error"
          className="mb-4 shrink-0 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          {errorMessage}
        </div>
      ) : null}

      <div
        ref={messageListRef}
        className="min-h-0 flex-1 space-y-4 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 sm:p-6"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {isLoadingHistory ? (
          <p className="text-center text-sm text-slate-500 sm:text-base">
            Loading conversation...
          </p>
        ) : messages.length === 0 ? (
          <p className="text-center text-sm text-slate-500 sm:text-base">
            Type a question below to start the conversation.
          </p>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              citations={message.citations}
              confidenceScore={message.confidenceScore}
              disclaimer={message.disclaimer}
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
          disabled={isSending || isLoadingHistory}
          className="w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 outline-none ring-indigo-500 placeholder:text-slate-400 focus:ring-2 disabled:cursor-not-allowed disabled:bg-slate-100 sm:text-base"
        />
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            disabled={!canSend}
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300 sm:text-base"
          >
            {isSending ? "Sending..." : "Send"}
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
