const LEGACY_TOKEN_KEYS = ["playnest_access_token", "playnest_refresh_token"];

type SessionInvalidationListener = () => void;

let accessToken: string | null = null;
let sessionGeneration = 0;
const invalidationListeners = new Set<SessionInvalidationListener>();

function notifySessionInvalidated() {
  invalidationListeners.forEach((listener) => listener());
}

export function purgeLegacyBrowserTokens() {
  if (typeof window === "undefined") return;

  for (const storageName of ["localStorage", "sessionStorage"] as const) {
    try {
      const storage = window[storageName];
      for (const key of LEGACY_TOKEN_KEYS) storage.removeItem(key);
    } catch {
      // Storage can be unavailable in hardened/private browser contexts.
    }
  }
}

export function getAccessToken() {
  return accessToken;
}

export function getSessionGeneration() {
  return sessionGeneration;
}

export function setAccessTokenIfCurrent(token: string, generation: number) {
  if (generation !== sessionGeneration) return false;
  accessToken = token;
  return true;
}

export function replaceSessionAccessToken(token: string) {
  sessionGeneration += 1;
  accessToken = token;
  return sessionGeneration;
}

export function invalidateSession() {
  sessionGeneration += 1;
  accessToken = null;
  purgeLegacyBrowserTokens();
  notifySessionInvalidated();
}

export function clearTokens() {
  invalidateSession();
}

export function subscribeToSessionInvalidation(
  listener: SessionInvalidationListener,
) {
  invalidationListeners.add(listener);
  return () => invalidationListeners.delete(listener);
}
