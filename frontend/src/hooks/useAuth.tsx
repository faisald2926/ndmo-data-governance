"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import type { User } from "@/types";
import { loadSession, clearSession, saveSession } from "@/lib/auth";
import { canAccessRoute } from "@/lib/rbac";

interface AuthContextValue {
  user: User | null;
  setUser: (u: User | null) => void;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  setUser: () => {},
  logout: () => {},
  loading: true,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Load session from localStorage on first mount (client only)
  useEffect(() => {
    const session = loadSession();
    setUserState(session);
    setLoading(false);
  }, []);

  // Route guard — only runs after loading is done
  useEffect(() => {
    if (loading) return;

    if (!user && pathname !== "/login") {
      router.replace("/login");
      return;
    }

    if (user && pathname === "/login") {
      router.replace("/dashboard");
      return;
    }

    if (user && pathname !== "/login") {
      if (!canAccessRoute(user.role, pathname)) {
        router.replace("/dashboard");
      }
    }
  }, [user, loading, pathname, router]);

  function setUser(u: User | null) {
    if (u) saveSession(u);
    setUserState(u);
  }

  function logout() {
    clearSession();
    setUserState(null);
    router.replace("/login");
  }

  return (
    <AuthContext.Provider value={{ user, setUser, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
