import type { User, Role } from "@/types";

// ── Demo users (replace with real JWT when FastAPI adds /auth/token) ──────────
// Each user has a hardcoded role so the competition demo works out-of-the-box.
export const DEMO_USERS: Record<string, { password: string; user: User }> = {
  admin: {
    password: "admin123",
    user: { id: "1", username: "admin", role: "admin", display_name: "مدير النظام" },
  },
  reviewer: {
    password: "reviewer123",
    user: { id: "2", username: "reviewer", role: "reviewer", display_name: "مراجع التصنيف" },
  },
  analyst: {
    password: "analyst123",
    user: { id: "3", username: "analyst", role: "analyst", display_name: "محلل البيانات" },
  },
  viewer: {
    password: "viewer123",
    user: { id: "4", username: "viewer", role: "viewer", display_name: "مستخدم عام" },
  },
};

export function login(username: string, password: string): User | null {
  const entry = DEMO_USERS[username];
  if (!entry || entry.password !== password) return null;
  return entry.user;
}

export function saveSession(user: User): void {
  localStorage.setItem("ndmo_user", JSON.stringify(user));
}

export function loadSession(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("ndmo_user");
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function clearSession(): void {
  localStorage.removeItem("ndmo_user");
  localStorage.removeItem("ndmo_token");
}

export const ROLE_LABELS: Record<Role, string> = {
  admin:    "مدير النظام",
  reviewer: "مراجع التصنيف",
  analyst:  "محلل البيانات",
  viewer:   "مستخدم عام",
};
