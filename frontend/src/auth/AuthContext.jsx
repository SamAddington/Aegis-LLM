import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, onUnauthorized, tokenStorage } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authConfig, setAuthConfig] = useState({ allow_registration: true });

  const loadMe = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    onUnauthorized(() => setUser(null));

    (async () => {
      try {
        const cfg = await api.authConfig();
        setAuthConfig(cfg);
      } catch {
        /* non-fatal */
      }
      if (tokenStorage.get()) await loadMe();
      setLoading(false);
    })();
  }, [loadMe]);

  const login = useCallback(
    async (username, password) => {
      const res = await api.login(username, password);
      tokenStorage.set(res.access_token);
      setUser(res.user);
      return res.user;
    },
    []
  );

  const register = useCallback(async (payload) => {
    const res = await api.register(payload);
    tokenStorage.set(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      authConfig,
      isAdmin: user?.role === "admin",
      login,
      register,
      logout,
      refresh: loadMe,
    }),
    [user, loading, authConfig, login, register, logout, loadMe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
