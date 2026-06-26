"use client";

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Topbar } from "@/components/layout/Topbar";
import { ScrollText } from "lucide-react";

interface AuditEntry {
  id: number;
  action: string;
  detail: Record<string, unknown>;
  created_at: string;
}

async function fetchAuditLog(): Promise<AuditEntry[]> {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const token = typeof window !== "undefined" ? localStorage.getItem("ndmo_token") : null;
  const { data } = await axios.get<AuditEntry[]>(`${base}/audit-log`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    params: { limit: 200 },
  });
  return data;
}

export default function AuditLogPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-log"],
    queryFn: fetchAuditLog,
    retry: false,
  });

  return (
    <div>
      <Topbar
        title="سجل التدقيق"
        subtitle="سجل كامل وغير قابل للتعديل لجميع إجراءات الحوكمة"
      />

      <div className="p-6 space-y-4">
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-900 border-t-transparent" />
          </div>
        )}

        {isError && (
          /* The /audit-log endpoint may not yet be wired in FastAPI.
             Show a helpful placeholder so the page doesn't break. */
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 gap-3">
            <ScrollText className="h-10 w-10 text-gray-300" strokeWidth={1.5} />
            <p className="text-sm font-medium text-gray-500">
              نقطة النهاية <code className="text-xs bg-gray-100 px-1 rounded">/audit-log</code> لم تُضف بعد إلى FastAPI
            </p>
            <p className="text-xs text-gray-400 max-w-xs text-center">
              أضف الـ endpoint إلى <code>app/main.py</code> وسيظهر السجل هنا تلقائياً.
            </p>
          </div>
        )}

        {data && data.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 gap-3">
            <ScrollText className="h-10 w-10 text-gray-300" strokeWidth={1.5} />
            <p className="text-sm text-gray-400">لا توجد إدخالات في السجل بعد</p>
          </div>
        )}

        {data && data.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    {["#", "الإجراء", "التفاصيل", "التوقيت"].map((h) => (
                      <th
                        key={h}
                        className="px-4 py-3 text-right text-xs font-semibold text-gray-500"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.map((entry) => (
                    <tr
                      key={entry.id}
                      className="border-b border-gray-50 hover:bg-gray-50/50"
                    >
                      <td className="px-4 py-3 text-xs text-gray-400 font-mono">
                        {entry.id}
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded-md bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                          {entry.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 max-w-[400px] truncate text-xs text-gray-500 font-mono">
                        {JSON.stringify(entry.detail)}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 font-mono whitespace-nowrap">
                        {new Date(entry.created_at).toLocaleString("ar-SA", {
                          dateStyle: "short",
                          timeStyle: "medium",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
