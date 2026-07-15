/**
 * Top-level chat container — state orchestration for the Judicial Editorial UI.
 * See TASKS.md T43/T45/T46/T47 and the frontend UI plan.
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
import ChatHeader from "@/components/layout/ChatHeader";
import DisclaimerStrip, {
  DEFAULT_CONSENT_TO_LOG,
} from "@/components/layout/DisclaimerStrip";
import EditorialHero from "@/components/layout/EditorialHero";
import ScrollReveal from "@/components/motion/ScrollReveal";
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
        if (!cancelled) {
          const message =
            error instanceof ApiClientError
              ? error.message
              : "Unable to load previous messages.";
          setErrorMessage(message);
          if (error instanceof ApiClientError) {
            setErrorStatus(error.status);
          }
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
    // Remove the failed trailing user message if present, then resend.
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

      <EditorialHero />

      <section id="legal-desk" className="scroll-mt-8 pb-24 pt-24 lg:pt-32">
        <ScrollReveal className="mb-12 grid gap-8 lg:grid-cols-[0.75fr_1.25fr] lg:items-end">
          <div>
            <p className="font-mono text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-burgundy">
              The legal research desk
            </p>
            <p className="mt-3 font-mono text-[0.62rem] uppercase tracking-[0.16em] text-ink-muted">
              Session · Private workspace
            </p>
          </div>
          <div>
            <h2 className="font-display max-w-4xl text-[clamp(3rem,6vw,6.5rem)] font-medium leading-[0.88] tracking-[-0.04em] text-ink">
              Ask plainly.
              <span className="block italic text-burgundy">
                Read critically.
              </span>
            </h2>
            <p className="mt-6 max-w-2xl text-base leading-7 text-ink-muted">
              Your answer and its evidence stay side by side. The conversation
              explains the law; the source ledger lets you verify it.
            </p>
          </div>
        </ScrollReveal>

        {errorMessage ? (
          <ErrorAlert
            message={errorMessage}
            status={errorStatus}
            onRetry={lastOutgoingPayload ? () => void handleRetry() : undefined}
          />
        ) : null}

        <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
          <ScrollReveal direction="left" className="min-w-0">
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
          </ScrollReveal>

          <ScrollReveal direction="right" delay={100} className="h-full">
            <CitationPanel
              citations={panelCitations}
              confidenceScore={activeAssistant?.confidenceScore}
              legalDomain={activeAssistant?.legalDomain}
              isRefusal={activeAssistant?.isRefusal}
            />
          </ScrollReveal>
        </div>
      </section>

      <ScrollReveal>
        <footer className="grid gap-8 border-t border-ink/15 py-10 sm:grid-cols-2 sm:items-end">
          <div>
            <p className="font-display text-3xl font-semibold">Nyāya</p>
            <p className="mt-2 max-w-sm text-sm leading-6 text-ink-muted">
              Explainable legal research for Indian statute. Not a substitute
              for licensed counsel.
            </p>
          </div>
          <div className="font-mono text-[0.6rem] uppercase tracking-[0.18em] text-ink-muted sm:text-right">
            Six legal domains · Primary-source citations · Honest uncertainty
          </div>
        </footer>
      </ScrollReveal>

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
