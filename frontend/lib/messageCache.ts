/**
 * In-memory cache of assistant message metadata (citations, confidence, etc.)
 * keyed by content hash. Cleared automatically on page refresh.
 */
import type { SourceCitation } from "@/lib/types";

export interface CachedAssistantMeta {
  citations: SourceCitation[];
  confidenceScore: number;
  legalDomain?: string;
  isRefusal?: boolean;
  disclaimer?: string;
}

const cache = new Map<string, CachedAssistantMeta>();

function hashContent(content: string): string {
  let hash = 0;
  for (let i = 0; i < content.length; i += 1) {
    hash = (hash << 5) - hash + content.charCodeAt(i);
    hash |= 0;
  }
  return `${hash}`;
}

function storageKey(content: string): string {
  return `${content.length}.${hashContent(content)}`;
}

export function cacheAssistantMeta(
  content: string,
  meta: CachedAssistantMeta
): void {
  cache.set(storageKey(content), meta);
}

export function getCachedAssistantMeta(
  content: string
): CachedAssistantMeta | null {
  return cache.get(storageKey(content)) ?? null;
}

/** Test helper to reset in-memory cache state. */
export function clearMessageCache(): void {
  cache.clear();
}
