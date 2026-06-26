"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Table2,
  ShieldCheck,
  BarChart2,
  GitBranch,
  Wand2,
  Play,
  ScrollText,
  LogOut,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { canAccessRoute } from "@/lib/rbac";
import { ROLE_LABELS } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard",  label: "نظرة عامة",       icon: LayoutDashboard },
  { href: "/records",    label: "السجلات",          icon: Table2         },
  { href: "/quality",    label: "الجودة",           icon: ShieldCheck    },
  { href: "/evaluation", label: "التقييم",          icon: BarChart2      },
  { href: "/lineage",    label: "الأثر (Lineage)",  icon: GitBranch      },
  { href: "/classify",   label: "تصنيف مباشر",      icon: Wand2          },
  { href: "/pipeline",   label: "خط المعالجة",      icon: Play           },
  { href: "/audit-log",  label: "سجل التدقيق",      icon: ScrollText     },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const visibleNav = NAV_ITEMS.filter((item) =>
    canAccessRoute(user.role, item.href)
  );

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-gray-200 bg-white">
      {/* Logo */}
      <div className="flex items-center gap-2.5 border-b border-gray-100 px-5 py-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-900">
          <Shield className="h-4 w-4 text-white" strokeWidth={2} />
        </div>
        <div>
          <p className="text-sm font-semibold text-gray-900 leading-none">
            NDMO حوكمة
          </p>
          <p className="text-xs text-gray-400 leading-none mt-0.5">
            Data Governance
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-0.5">
          {visibleNav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-blue-50 text-blue-900 font-medium"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                  dir="rtl"
                >
                  <Icon
                    className={cn(
                      "h-4 w-4 flex-shrink-0",
                      active ? "text-blue-600" : "text-gray-400"
                    )}
                    strokeWidth={1.75}
                  />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User footer */}
      <div className="border-t border-gray-100 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-gray-900">
              {user.display_name}
            </p>
            <p className="text-xs text-gray-400">
              {ROLE_LABELS[user.role]}
            </p>
          </div>
          <button
            onClick={logout}
            className="ml-2 rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
            title="تسجيل الخروج"
          >
            <LogOut className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>
      </div>
    </aside>
  );
}
