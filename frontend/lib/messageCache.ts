/**
 * Client-side cache of assistant message metadata (citations, confidence, etc.)
 * keyed by content hash — mitigates history reload gap until the backend
 * extends the session history API.
 */
import type { SourceCitation } from "@/lib/types";

const CACHE_PREFIX = "ai-legal-assistant.msg-meta.";

export interface CachedAssistantMeta {
  citations: SourceCitation[];
  confidenceScore: number;
  legalDomain?: string;
  isRefusal?: boolean;
  disclaimer?: string;
}

function hashContent(content: string): string {
  let hash = 0;
  for (let i = 0; i < content.length; i += 1) {
    hash = (hash << 5) - hash + content.charCodeAt(i);
    hash |= 0;
  }
  return `${hash}`;
}

function storageKey(content: string): string {
  // Length materially reduces accidental collisions in the small 32-bit hash.
  return `${CACHE_PREFIX}${content.length}.${hashContent(content)}`;
}

export function cacheAssistantMeta(
  content: string,
  meta: CachedAssistantMeta
): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    sessionStorage.setItem(storageKey(content), JSON.stringify(meta));
  } catch {
    // Ignore quota / private-mode failures.
  }
}

export function getCachedAssistantMeta(
  content: string
): CachedAssistantMeta | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = sessionStorage.getItem(storageKey(content));
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as CachedAssistantMeta;
  } catch {
    return null;
  }
}
