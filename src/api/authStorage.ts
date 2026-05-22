const STORAGE_KEY = 'oform_auth_v2';

export type StoredAuth = {
  userId: string;
  email: string;
  accessToken: string;
};

export function loadStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const u = JSON.parse(raw) as Record<string, unknown>;
    if (
      typeof u.userId === 'string' &&
      typeof u.email === 'string' &&
      typeof u.accessToken === 'string' &&
      u.accessToken.length > 0
    ) {
      return { userId: u.userId, email: u.email, accessToken: u.accessToken };
    }
  } catch {
    /* ignore */
  }
  return null;
}

export function saveStoredAuth(auth: StoredAuth | null) {
  if (!auth) localStorage.removeItem(STORAGE_KEY);
  else localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
}

export function getAccessToken(): string | null {
  return loadStoredAuth()?.accessToken ?? null;
}
