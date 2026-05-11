import { useState, useEffect, useCallback } from "react";
import { getToken, setToken, clearToken, decodeToken, loginWithPassword } from "@/lib/fastapi";

export type AuthUser = { id: string; role: string };

function readUser(): AuthUser | null {
  const t = getToken();
  if (!t) return null;
  const payload = decodeToken(t);
  if (!payload) return null;
  // Check expiry
  if (payload.exp && payload.exp * 1000 < Date.now()) {
    clearToken();
    return null;
  }
  return { id: payload.sub, role: payload.role };
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(readUser);
  const loading = false;

  // Re-check on storage events (multi-tab support)
  useEffect(() => {
    const handler = () => setUser(readUser());
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const token = await loginWithPassword(email, password);
    setToken(token);
    setUser(readUser());
  }, []);

  const signOut = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  return {
    user,
    // Lovable-compatible shape so AppShell works unchanged
    session: user ? { user: { id: user.id, email: "" } } : null,
    loading,
    signIn,
    signOut,
  };
}
