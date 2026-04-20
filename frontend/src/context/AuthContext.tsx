import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { getMe, login as loginRequest } from '../api/auth';
import { ApiError } from '../api/client';
import { clearStoredToken, getStoredToken, setStoredToken } from '../lib/storage';
import type { AuthUser, LoginPayload } from '../types/auth';

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  };

  const refreshMe = async () => {
    const storedToken = getStoredToken();
    if (!storedToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const me = await getMe();
      setUser(me);
      setToken(storedToken);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        logout();
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const login = async (payload: LoginPayload) => {
    const data = await loginRequest(payload);
    setStoredToken(data.access_token);
    setToken(data.access_token);
    const me = await getMe();
    setUser(me);
  };

  useEffect(() => {
    void refreshMe().catch(() => undefined);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshMe,
    }),
    [token, user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
