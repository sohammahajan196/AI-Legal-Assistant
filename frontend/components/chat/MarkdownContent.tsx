/**
 * Renders assistant answer text as Markdown while preserving cream-panel typography.
 */
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { normalizeAnswerText } from "@/lib/normalizeAnswerText";

export interface MarkdownContentProps {
  content: string;
  className?: string;
}

export default function MarkdownContent({
  content,
  className = "",
}: MarkdownContentProps) {
  const normalized = normalizeAnswerText(content);

  return (
    <div
      className={`markdown-answer break-words ${className}`.trim()}
      data-testid="markdown-answer"
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => (
            <p className="mb-3 last:mb-0 [&:not(:first-child)]:mt-0">{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-ink-cream">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          ol: ({ children }) => (
            <ol className="mb-3 list-decimal space-y-2 pl-5 last:mb-0">{children}</ol>
          ),
          ul: ({ children }) => (
            <ul className="mb-3 list-disc space-y-2 pl-5 last:mb-0">{children}</ul>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          a: ({ href, children }) => (
            <a
              href={href}
              className="underline decoration-[var(--border-cream)] underline-offset-2 hover:text-ink-cream"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
