/**
 * Ephemeral session id for multi-turn chat within a single page load.
 * A fresh id is created on every mount — nothing is persisted to browser storage.
 */

export function createSessionId(): string {
  return crypto.randomUUID();
}
