import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setAuthLostHandler, tokens } from "../services/api";
import type { User } from "../types";

interface AuthState {
  user: User | null; loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
}
const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const qc = useQueryClient();

  const loadMe = useCallback(async () => { setUser(await api<User>("/users/me")); }, []);

  useEffect(() => {
    setAuthLostHandler(() => { setUser(null); qc.clear(); });
    const rt = tokens.refresh();
    if (!rt) { setLoading(false); return; }
    // Restore the session after a page reload using the refresh token.
    fetch("/api/v1/auth/refresh", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: rt }) })
      .then(async (r) => { if (!r.ok) throw new Error("expired"); const t = await r.json(); tokens.set(t.access_token, t.refresh_token); await loadMe(); })
      .catch(() => tokens.clear())
      .finally(() => setLoading(false));
  }, [loadMe, qc]);

  const login = useCallback(async (email: string, password: string) => {
    const t = await api<{ access_token: string; refresh_token: string }>("/auth/login", { json: { email, password } });
    tokens.set(t.access_token, t.refresh_token);
    await loadMe();
  }, [loadMe]);

  const logout = useCallback(async () => {
    try { await api("/auth/logout", { method: "POST" }); } catch { /* best effort */ }
    tokens.clear(); setUser(null); qc.clear();
  }, [qc]);

  const value = useMemo<AuthState>(() => ({
    user, loading, login, logout, hasRole: (...r) => !!user && r.some((x) => user.role_names.includes(x)),
  }), [user, loading, login, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}
