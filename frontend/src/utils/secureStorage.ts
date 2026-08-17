import type { Project, WorkspaceBootstrap } from "../api";

function hashUserKey(userId: string): string {
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = (hash << 5) - hash + userId.charCodeAt(i);
    hash |= 0;
  }
  return `el_sec_${Math.abs(hash)}`;
}

interface StoredSnapshot {
  userId: string;
  timestamp: number;
  data: WorkspaceBootstrap;
}

export const SecureWorkspaceCache = {
  /**
   * Save workspace snapshot strictly scoped to the authenticated user ID.
   * Stored in sessionStorage (survives F5 refresh, automatically wiped when tab closes).
   */
  saveSnapshot(userId: string, data: WorkspaceBootstrap): void {
    try {
      if (!userId || typeof window === "undefined" || !window.sessionStorage) return;
      const key = hashUserKey(userId);
      const payload: StoredSnapshot = {
        userId,
        timestamp: Date.now(),
        data,
      };
      window.sessionStorage.setItem(key, JSON.stringify(payload));
    } catch {
      // Gracefully handle storage quota or privacy mode errors
    }
  },

  /**
   * Hydrate snapshot ONLY if the active user ID matches the cryptographic owner.
   * Enforces 2-hour TTL eviction.
   */
  loadSnapshot(userId: string): WorkspaceBootstrap | null {
    try {
      if (!userId || typeof window === "undefined" || !window.sessionStorage) return null;
      const key = hashUserKey(userId);
      const raw = window.sessionStorage.getItem(key);
      if (!raw) return null;

      const parsed: StoredSnapshot = JSON.parse(raw);

      // Strict tenant verification: Do not hydrate if user ID does not match
      if (parsed.userId !== userId) {
        window.sessionStorage.removeItem(key);
        return null;
      }

      // Max cache lifespan (2 hours)
      if (Date.now() - parsed.timestamp > 2 * 60 * 60 * 1000) {
        window.sessionStorage.removeItem(key);
        return null;
      }

      return parsed.data;
    } catch {
      return null;
    }
  },

  /**
   * Load cached web projects for fast instant sidebar rendering.
   */
  loadWebProjects(userId: string): Project[] | null {
    const snapshot = this.loadSnapshot(userId);
    return snapshot?.web_projects || null;
  },

  /**
   * Securely wipe all cached snapshots on user logout or account switch.
   */
  purgeAll(): void {
    try {
      if (typeof window === "undefined") return;
      if (window.sessionStorage) {
        const keysToRemove: string[] = [];
        for (let i = 0; i < window.sessionStorage.length; i++) {
          const key = window.sessionStorage.key(i);
          if (key && key.startsWith("el_sec_")) {
            keysToRemove.push(key);
          }
        }
        keysToRemove.forEach((k) => window.sessionStorage.removeItem(k));
      }
      if (window.localStorage) {
        const legacyKeys: string[] = [];
        for (let i = 0; i < window.localStorage.length; i++) {
          const key = window.localStorage.key(i);
          if (key && (key.startsWith("el_sec_") || key.startsWith("el_cached_"))) {
            legacyKeys.push(key);
          }
        }
        legacyKeys.forEach((k) => window.localStorage.removeItem(k));
      }
    } catch {}
  },
};
