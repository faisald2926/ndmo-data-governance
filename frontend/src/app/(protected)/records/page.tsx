"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Lock, Search } from "lucide-react";
import { fetchRecords } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { canSeeLevel } from "@/lib/rbac";
import { SensitivityBadge } from "@/components/ui/SensitivityBadge";
import { MaskedCell } from "@/components/ui/MaskedCell";
import { Topbar } from "@/components/layout/Topbar";
import { LEVELS } from "@/types";
import type { NdmoLevel } from "@/types";
import { formatConfidence, cn } from "@/lib/utils";

export default function RecordsPage() {
  const { user } = useAuth();
  const [filterLevel, setFilterLevel] = useState<"" | NdmoLevel>("");
  const [filterSource, setFilterSource] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["records", filterLevel, filterSource],
    queryFn: () =>
      fetchRecords({
        level: filterLevel || undefined,
        source_file: filterSource || undefined,
        limit: 200,
      }),
    enabled: !!user,
  });

  const role = user?.role ?? "viewer";

  // Filter out levels the user can't see
  const visible = (data ?? []).filter((r) => canSeeLevel(role, r.ndmo_level));

  return (
    <div>
      <Topbar
        title="السجلات المصنّفة"
        subtitle={`${visible.length} سجل معروض`}
      />

      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value as "" | NdmoLevel)}
            className="rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">كل المستويات</option>
            {LEVELS.filter((l) => canSeeLevel(role, l)).map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>

          <div className="relative flex-1 min-w-[200px]">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
              strokeWidth={1.75}
            />
            <input
              type="text"
              placeholder="بحث بالملف المصدر…"
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-9 pr-3.5 text-sm text-gray-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              dir="ltr"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  {[
                    "رقم السجل",
                    "الملف المصدر",
                    "مستوى التصنيف",
                    "فئة الأثر",
                    "الثقة",
                    "تقرر بواسطة",
                    "مراجعة بشرية",
                    "التوصية",
                  ].map((h) => (
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
                {isLoading ? (
                  Array.from({ length: 8 }).map((_, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j} className="px-4 py-3">
                          <div className="h-4 animate-pulse rounded bg-gray-100" />
                        </td>
                      ))}
                    </tr>
                  ))
                ) : visible.length === 0 ? (
                  <tr>
                    <td
                      colSpan={8}
                      className="py-16 text-center text-sm text-gray-400"
                    >
                      لا توجد سجلات — شغّل خط المعالجة أولاً
                    </td>
                  </tr>
                ) : (
                  visible.map((row, i) => {
                    // Top-secret rows: show locked placeholder for analyst/viewer
                    if (
                      row.ndmo_level === "سري للغاية" &&
                      (role === "analyst" || role === "viewer")
                    ) {
                      return (
                        <tr
                          key={i}
                          className="border-b border-gray-50 bg-red-50/30"
                        >
                          <td
                            colSpan={8}
                            className="px-4 py-3 text-center text-xs text-red-400"
                          >
                            <span className="inline-flex items-center gap-1.5">
                              <Lock className="h-3 w-3" strokeWidth={2} />
                              سجل مصنّف «سري للغاية» — غير متاح لصلاحيتك
                            </span>
                          </td>
                        </tr>
                      );
                    }

                    return (
                      <tr
                        key={i}
                        className={cn(
                          "border-b border-gray-50 transition-colors hover:bg-gray-50/50",
                          row.needs_review && "bg-amber-50/30"
                        )}
                      >
                        <td className="px-4 py-3 font-mono text-xs text-gray-500">
                          <MaskedCell
                            value={row.record_id}
                            column="record_id"
                            role={role}
                            level={row.ndmo_level}
                          />
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-xs">
                          {row.source_file}
                        </td>
                        <td className="px-4 py-3">
                          <SensitivityBadge level={row.ndmo_level} size="sm" />
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {row.impact_category || "—"}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {formatConfidence(row.confidence)}
                        </td>
                        <td className="px-4 py-3">
                          <span className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600 font-mono">
                            {row.decided_by}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {row.needs_review ? (
                            <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600">
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                              نعم
                            </span>
                          ) : (
                            <span className="text-xs text-gray-400">لا</span>
                          )}
                        </td>
                        <td className="px-4 py-3 max-w-[200px] truncate text-xs text-gray-500">
                          {row.control_recommendation || "—"}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
