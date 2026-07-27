import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthState>(null as unknown as AuthState);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const { data } = await api.get<User>("/auth/me");
      setUser(data);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const { data } = await api.post<User>("/auth/login", { username, password });
    setUser(data);
  };

  const logout = async () => {
    const wasSso = user?.is_sso ?? false;
    await api.post("/auth/logout");
    setUser(null);
    if (wasSso) {
      // This app's own session cookie is irrelevant for an SSO user — the
      // Remote-User header re-authenticates them on the very next request
      // regardless of it. The only real "log out" is ending the Authelia
      // session itself, which then makes nginx's auth_request bounce back
      // to the actual unified login page instead of this app's own (which
      // an SSO user's account can never log into: its password is random
      // and never issued).
      await fetch("/authelia/api/logout", { method: "POST", credentials: "include" });
      window.location.href = "/weekly_report/";
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
