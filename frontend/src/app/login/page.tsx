"use client";

import { useState, FormEvent } from "react";
import { Shield, Eye, EyeOff } from "lucide-react";
import { login, DEMO_USERS } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const { setUser } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    setTimeout(() => {
      const user = login(username, password);
      if (!user) {
        setError("اسم المستخدم أو كلمة المرور غير صحيحة");
        setLoading(false);
        return;
      }
      // setUser saves to localStorage AND updates context → triggers route guard → redirect
      setUser(user);
    }, 400);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-900 shadow-md">
            <Shield className="h-7 w-7 text-white" strokeWidth={1.75} />
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">
            منصة حوكمة البيانات
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            المكتب الوطني لإدارة البيانات — NDMO
          </p>
        </div>

        {/* Form card */}
        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="username"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                اسم المستخدم
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                dir="ltr"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-gray-700"
              >
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  dir="ltr"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  {showPw ? (
                    <EyeOff className="h-4 w-4" strokeWidth={1.75} />
                  ) : (
                    <Eye className="h-4 w-4" strokeWidth={1.75} />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p className="rounded-lg bg-red-50 px-3.5 py-2.5 text-sm text-red-700 border border-red-200">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className={cn(
                "w-full rounded-lg bg-blue-900 py-2.5 text-sm font-medium text-white transition-colors",
                loading
                  ? "opacity-60 cursor-not-allowed"
                  : "hover:bg-blue-800 active:bg-blue-900"
              )}
            >
              {loading ? "جارٍ تسجيل الدخول…" : "تسجيل الدخول"}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-6 border-t border-gray-100 pt-5">
            <p className="mb-3 text-xs font-medium text-gray-400 text-center">
              حسابات تجريبية (للعرض التوضيحي)
            </p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(DEMO_USERS).map(([uname, { user, password: pw }]) => (
                <button
                  key={uname}
                  type="button"
                  onClick={() => {
                    setUsername(uname);
                    setPassword(pw);
                  }}
                  className="rounded-lg border border-gray-200 px-3 py-2 text-left text-xs hover:border-blue-300 hover:bg-blue-50 transition-colors"
                  dir="rtl"
                >
                  <span className="block font-medium text-gray-700">
                    {user.display_name}
                  </span>
                  <span className="text-gray-400">{uname}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
