/**
 * Chat composer — textarea + send, Enter to send / Shift+Enter newline.
 */
"use client";

import { FormEvent, KeyboardEvent } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  isSending?: boolean;
}

export default function ChatComposer({
  value,
  onChange,
  onSubmit,
  disabled = false,
  isSending = false,
}: ChatComposerProps) {
  const canSend = value.trim().length > 0 && !disabled && !isSending;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSend) {
      onSubmit();
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) {
        onSubmit();
      }
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="sticky bottom-4 z-20 mx-2 mt-5 rounded-[1.4rem] border border-warm bg-surface/95 p-3 shadow-[0_20px_60px_rgb(48_35_24/18%)] backdrop-blur-xl sm:mx-5 sm:p-4"
    >
      <label htmlFor="chat-input" className="sr-only">
        Your message
      </label>
      <Textarea
        id="chat-input"
        rows={2}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about Indian law..."
        disabled={disabled || isSending}
        className="min-h-[78px] max-h-40 resize-none border-0 bg-transparent px-2 text-[0.95rem] leading-6 text-ink shadow-none placeholder:text-ink-muted/70 focus-visible:ring-0"
      />
      <div className="mt-2 flex items-center justify-between border-t border-warm px-1 pt-3">
        <p className="hidden font-mono text-[0.58rem] uppercase tracking-[0.15em] text-ink-muted sm:block">
          Enter to send · Shift + Enter for a new line
        </p>
        <Button
          type="submit"
          disabled={!canSend}
          className="ml-auto min-h-11 rounded-full bg-burgundy px-5 shadow-[0_8px_20px_rgb(113_47_56/20%)] hover:-translate-y-0.5 hover:bg-burgundy/90"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
          <span>{isSending ? "Sending..." : "Send"}</span>
        </Button>
      </div>
    </form>
  );
}
