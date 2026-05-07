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
    // KHÔNG dùng window.location.href ở đây
    // React Router + ProtectedRoute sẽ tự redirect về /login khi user = null
  };

  const refreshMe = async () => {
    const storedToken = getStoredToken();

    // Không có token → dừng loading, không gọi API
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setLoading(false);
      return;
    }

    try {
      const me = await getMe();
      setUser(me);
      setToken(storedToken);
    } catch (error) {
      // Token hết hạn hoặc không hợp lệ → logout sạch
      // logout() sẽ xóa localStorage và set state về null
      // ProtectedRoute sẽ redirect về /login tự động
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
        logout();
        return; // QUAN TRỌNG: return sớm, không throw
      }
      // Lỗi khác (network, server...) → vẫn logout để an toàn
      logout();
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
    void refreshMe();
    // Không cần .catch() vì refreshMe đã tự xử lý mọi lỗi bên trong
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
    throw new Error('useAuth phải được dùng bên trong AuthProvider');
  }
  return context;
}