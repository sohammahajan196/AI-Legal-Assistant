/**
 * Top-level chat container — minimal dark chat-first UI.
 * See TASKS.md T43/T45/T46/T47.
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import ChatComposer from "@/components/chat/ChatComposer";
import ErrorAlert from "@/components/chat/ErrorAlert";
import MessageList, {
  type ChatMessageView,
} from "@/components/chat/MessageList";
import CitationPanel from "@/components/CitationPanel";
import AppShell from "@/components/layout/AppShell";
import AppFooter from "@/components/layout/AppFooter";
import ChatHeader from "@/components/layout/ChatHeader";
import DisclaimerStrip, {
  DEFAULT_CONSENT_TO_LOG,
} from "@/components/layout/DisclaimerStrip";
import {
  DEFAULT_USER_TYPE,
  type UserType,
} from "@/components/UserTypeSelector";
import {
  ApiClientError,
  fetchSessionHistory,
  sendChatMessage,
} from "@/lib/apiClient";
import {
  buildChatRequestPayload,
  type ChatApiRequestBody,
} from "@/lib/chatPayload";
import {
  cacheAssistantMeta,
  getCachedAssistantMeta,
} from "@/lib/messageCache";
import { getOrCreateSessionId } from "@/lib/sessionStorage";
import type { SourceCitation } from "@/lib/types";

interface ChatMessage extends ChatMessageView {}

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [consentToLog, setConsentToLog] = useState(DEFAULT_CONSENT_TO_LOG);
  const [userType, setUserType] = useState<UserType>(DEFAULT_USER_TYPE);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorStatus, setErrorStatus] = useState<number | undefined>();
  const [lastOutgoingPayload, setLastOutgoingPayload] =
    useState<ChatApiRequestBody | null>(null);
  const messageListRef = useRef<HTMLDivElement>(null);

  const activeAssistant = [...messages]
    .reverse()
    .find((m) => m.role === "assistant");

  const scrollToBottom = useCallback(() => {
    const list = messageListRef.current;
    if (!list) {
      return;
    }
    list.scrollTop = list.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending, scrollToBottom]);

  useEffect(() => {
    let cancelled = false;
    const activeSessionId = getOrCreateSessionId();
    setSessionId(activeSessionId);

    async function loadSessionHistory() {
      try {
        const history = await fetchSessionHistory(activeSessionId);
        if (cancelled) {
          return;
        }

        setMessages(
          history.map((message) => {
            const base: ChatMessage = {
              id: crypto.randomUUID(),
              role: message.role,
              content: message.content,
            };
            if (message.role === "assistant") {
              const cached = getCachedAssistantMeta(message.content);
              if (cached) {
                return {
                  ...base,
                  citations: cached.citations,
                  confidenceScore: cached.confidenceScore,
                  legalDomain: cached.legalDomain,
                  isRefusal: cached.isRefusal,
                  disclaimer: cached.disclaimer,
                };
              }
            }
            return base;
          })
        );
      } catch (error) {
        if (cancelled) {
          return;
        }
        // New/unknown sessions and a down backend should not block the desk.
        const status = error instanceof ApiClientError ? error.status : undefined;
        if (status === 404) {
          setMessages([]);
        } else {
          const message =
            error instanceof ApiClientError
              ? error.message
              : "Unable to load previous messages.";
          setErrorMessage(message);
          setErrorStatus(status);
          setMessages([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingHistory(false);
        }
      }
    }

    void loadSessionHistory();

    // Safety: never leave the UI stuck on the skeleton forever.
    const safetyTimer = window.setTimeout(() => {
      if (!cancelled) {
        setIsLoadingHistory(false);
      }
    }, 6000);

    return () => {
      cancelled = true;
      window.clearTimeout(safetyTimer);
    };
  }, []);

  async function sendWithPayload(payload: {
    query: string;
    sessionId: string;
    userType: UserType;
    consentToLog: boolean;
  }) {
    const outgoingPayload = buildChatRequestPayload(payload);
    setLastOutgoingPayload(outgoingPayload);
    setErrorMessage(null);
    setErrorStatus(undefined);
    setIsSending(true);

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: payload.query,
    };
    setMessages((current) => [...current, userMessage]);

    try {
      const response = await sendChatMessage(payload);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        citations: response.citations,
        confidenceScore: response.confidence_score,
        legalDomain: response.legal_domain,
        isRefusal: response.is_refusal,
        disclaimer: response.disclaimer,
      };

      cacheAssistantMeta(response.answer, {
        citations: response.citations,
        confidenceScore: response.confidence_score,
        legalDomain: response.legal_domain,
        isRefusal: response.is_refusal,
        disclaimer: response.disclaimer,
      });

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : "Something went wrong while contacting the assistant.";
      setErrorMessage(message);
      if (error instanceof ApiClientError) {
        setErrorStatus(error.status);
      }
    } finally {
      setIsSending(false);
    }
  }

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || !sessionId || isSending || isLoadingHistory) {
      return;
    }

    setInput("");
    await sendWithPayload({
      query: trimmed,
      sessionId,
      userType,
      consentToLog,
    });
  }

  async function handleRetry() {
    if (!lastOutgoingPayload || !sessionId || isSending) {
      return;
    }
    setMessages((current) => {
      const last = current[current.length - 1];
      if (last?.role === "user" && last.content === lastOutgoingPayload.query) {
        return current.slice(0, -1);
      }
      return current;
    });
    await sendWithPayload({
      query: lastOutgoingPayload.query,
      sessionId,
      userType: lastOutgoingPayload.user_type as UserType,
      consentToLog: lastOutgoingPayload.consent_to_log,
    });
  }

  const panelCitations: SourceCitation[] = activeAssistant?.citations ?? [];

  return (
    <AppShell>
      <ChatHeader userType={userType} onUserTypeChange={setUserType} />

      <DisclaimerStrip
        consentToLog={consentToLog}
        onConsentChange={setConsentToLog}
      />

      <section id="legal-desk" className="pb-16 pt-6">
        <div className="mb-6 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <h1 className="font-display text-2xl font-medium tracking-tight text-ink sm:text-[1.75rem]">
            Ask a legal question.
          </h1>
          <p className="text-sm text-ink-muted">
            Answers include citations, confidence, and source excerpts.
          </p>
        </div>

        {errorMessage ? (
          <ErrorAlert
            message={errorMessage}
            status={errorStatus}
            onRetry={lastOutgoingPayload ? () => void handleRetry() : undefined}
          />
        ) : null}

        <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0">
            <MessageList
              messages={messages}
              isLoadingHistory={isLoadingHistory}
              isSending={isSending}
              listRef={messageListRef}
              onSelectPrompt={setInput}
            />

            <ChatComposer
              value={input}
              onChange={setInput}
              onSubmit={() => void handleSend()}
              disabled={isLoadingHistory || !sessionId}
              isSending={isSending}
            />
          </div>

          <CitationPanel
            citations={panelCitations}
            confidenceScore={activeAssistant?.confidenceScore}
            legalDomain={activeAssistant?.legalDomain}
            isRefusal={activeAssistant?.isRefusal}
          />
        </div>
      </section>

      <AppFooter />

      {lastOutgoingPayload ? (
        <output
          aria-hidden="true"
          data-testid="last-outgoing-payload"
          className="hidden"
        >
          {JSON.stringify(lastOutgoingPayload)}
        </output>
      ) : null}
    </AppShell>
  );
}
