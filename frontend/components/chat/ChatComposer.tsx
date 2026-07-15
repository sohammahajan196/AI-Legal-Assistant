/**
 * Chat composer — textarea + shader send button.
 */
"use client";

import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useId,
  useRef,
} from "react";
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hintId = useId();

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) {
      return;
    }

    textarea.style.height = "auto";
    const computedMaxHeight = Number.parseFloat(
      window.getComputedStyle(textarea).maxHeight
    );
    const maxHeight = Number.isFinite(computedMaxHeight)
      ? computedMaxHeight
      : 176;
    textarea.style.height = `${Math.max(
      56,
      Math.min(textarea.scrollHeight, maxHeight)
    )}px`;
  }, [value]);

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
      aria-label="Legal question composer"
      className="group mt-3 rounded-xl border border-[var(--border-cream)] bg-surface p-2 shadow-[0_1px_2px_rgb(0_0_0/8%)] transition-[border-color,box-shadow] focus-within:border-amber/70 focus-within:shadow-[0_0_0_3px_rgb(184_151_90/12%)] sm:p-2.5"
    >
      <label htmlFor="chat-input" className="sr-only">
        Your message
      </label>
      <Textarea
        ref={textareaRef}
        id="chat-input"
        rows={1}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about Indian law..."
        disabled={disabled || isSending}
        aria-describedby={hintId}
        className="min-h-14 max-h-44 resize-none overflow-y-auto border-0 bg-transparent px-3 py-2.5 text-[0.95rem] leading-6 text-ink-cream shadow-none placeholder:text-[var(--ink-on-cream-muted)] focus-visible:ring-0"
      />
      <div className="mt-1 flex items-center justify-between border-t border-[var(--border-cream)] px-1.5 pt-2">
        <p
          id={hintId}
          className="sr-only text-[0.68rem] text-ink-cream-muted sm:not-sr-only"
        >
          Enter to send · Shift + Enter for newline
        </p>
        <Button
          type="submit"
          disabled={!canSend}
          className="btn-shader ml-auto h-9 rounded-lg border-0 px-4 text-sm font-medium"
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
