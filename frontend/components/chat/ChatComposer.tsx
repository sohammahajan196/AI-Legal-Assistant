/**
 * Chat composer — textarea + shader send button.
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
      className="sticky bottom-4 z-20 mt-4 rounded-2xl border border-[var(--border-cream)] bg-surface p-3 shadow-[0_16px_40px_rgb(0_0_0/28%)] sm:p-4"
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
        className="min-h-[72px] max-h-36 resize-none border-0 bg-transparent px-2 text-[0.95rem] leading-6 text-ink-cream shadow-none placeholder:text-[var(--ink-on-cream-muted)] focus-visible:ring-0"
      />
      <div className="mt-2 flex items-center justify-between border-t border-[var(--border-cream)] px-1 pt-3">
        <p className="hidden text-[0.68rem] text-ink-cream-muted sm:block">
          Enter to send · Shift + Enter for newline
        </p>
        <Button
          type="submit"
          disabled={!canSend}
          className="btn-shader ml-auto min-h-10 rounded-full border-0 px-5 font-medium"
        >
          <Send className="relative z-[1] h-4 w-4" aria-hidden="true" />
          <span className="relative z-[1]">
            {isSending ? "Sending..." : "Send"}
          </span>
        </Button>
      </div>
    </form>
  );
}
