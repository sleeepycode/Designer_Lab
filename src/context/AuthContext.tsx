import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { authLogin, authMe, authRegister } from '@/api/client';
import { loadStoredAuth, saveStoredAuth, type StoredAuth } from '@/api/authStorage';

export type AuthUser = {
  userId: string;
  email: string;
  accessToken: string;
};

type AuthState = {
  user: AuthUser | null;
  authLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

function toAuthUser(stored: StoredAuth): AuthUser {
  return {
    userId: stored.userId,
    email: stored.email,
    accessToken: stored.accessToken,
  };
}

function userFromAuthResponse(res: { user_id: string; email: string; access_token: string }): AuthUser {
  const u: StoredAuth = {
    userId: res.user_id,
    email: res.email,
    accessToken: res.access_token,
  };
  saveStoredAuth(u);
  return toAuthUser(u);
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const stored = loadStoredAuth();
    return stored ? toAuthUser(stored) : null;
  });
  const [authLoading, setAuthLoading] = useState(() => Boolean(loadStoredAuth()));

  useEffect(() => {
    const stored = loadStoredAuth();
    if (!stored) {
      setAuthLoading(false);
      return;
    }
    let cancelled = false;
    void authMe()
      .then((me) => {
        if (cancelled) return;
        const next = userFromAuthResponse(me);
        setUser(next);
      })
      .catch(() => {
        if (cancelled) return;
        saveStoredAuth(null);
        setUser(null);
      })
      .finally(() => {
        if (!cancelled) setAuthLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authLogin(email, password);
    setUser(userFromAuthResponse(res));
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const res = await authRegister(email, password);
    setUser(userFromAuthResponse(res));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    saveStoredAuth(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      authLoading,
      login,
      register,
      logout,
    }),
    [user, authLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth outside AuthProvider');
  return ctx;
}
