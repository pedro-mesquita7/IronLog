import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { apiFetch } from '../shared/api';

interface AuthState {
  jwt: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [jwt, setJwt] = useState<string | null>(() => localStorage.getItem('ironlog_jwt'));

  const login = useCallback(async (token: string) => {
    const res = await apiFetch<{ jwt: string; expires_at: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
    localStorage.setItem('ironlog_jwt', res.jwt);
    localStorage.setItem('ironlog_jwt_expires', res.expires_at);
    setJwt(res.jwt);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('ironlog_jwt');
    localStorage.removeItem('ironlog_jwt_expires');
    setJwt(null);
  }, []);

  return (
    <AuthContext.Provider value={{ jwt, login, logout, isAuthenticated: !!jwt }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
