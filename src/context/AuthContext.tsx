import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

const STORAGE_KEY = 'oform_auth_v1';

export type AuthUser = {
  userId: string;
  email: string;
};

type AuthState = {
  user: AuthUser | null;
  login: (email: string, password: string) => void;
  register: (email: string, password: string) => void;
  logout: () => void;
};

function stableUserIdFromEmail(email: string): string {
  const norm = email.trim().toLowerCase();
  let h = 0;
  for (let i = 0; i < norm.length; i++) {
    h = (Math.imul(31, h) + norm.charCodeAt(i)) | 0;
  }
  return `u_${Math.abs(h).toString(16)}_${norm.length}`;
}

function loadUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const u = JSON.parse(raw) as Record<string, unknown>;
    if (typeof u.userId === 'string' && typeof u.email === 'string') {
      return { userId: u.userId, email: u.email };
    }
  } catch {
    /* ignore */
  }
  return null;
}

function saveUser(u: AuthUser | null) {
  if (!u) localStorage.removeItem(STORAGE_KEY);
  else localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => loadUser());

  const login = useCallback((email: string, _password: string) => {
    const trimmed = email.trim();
    const u: AuthUser = {
      userId: stableUserIdFromEmail(trimmed),
      email: trimmed,
    };
    setUser(u);
    saveUser(u);
  }, []);

  const register = useCallback(
    (email: string, password: string) => {
      login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    setUser(null);
    saveUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      login,
      register,
      logout,
    }),
    [user, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth outside AuthProvider');
  return ctx;
}
