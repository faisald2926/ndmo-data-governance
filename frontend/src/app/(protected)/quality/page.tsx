"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchQualityFindings } from "@/lib/api";
import { Topbar } from "@/components/layout/Topbar";
import { DIMENSIONS } from "@/types";
import type { DqDimension } from "@/types";

const DIM_COLORS: Record<string, string> = {
  Completeness:  "bg-blue-100 text-blue-800",
  Uniqueness:    "bg-purple-100 text-purple-800",
  Timeliness:    "bg-green-100 text-green-800",
  Validity:      "bg-red-100 text-red-800",
  Accuracy:      "bg-amber-100 text-amber-800",
  Consistency:   "bg-gray-100 text-gray-700",
};

export default function QualityPage() {
  const [dim, setDim] = useState<"" | DqDimension>("");

  const { data, isLoading } = useQuery({
    queryKey: ["quality", dim],
    queryFn: () =>
      fetchQualityFindings({
        dimension: dim || undefined,
        limit: 500,
      }),
  });

  return (
    <div>
      <Topbar
        title="تقرير جودة البيانات"
        subtitle={`${data?.length ?? 0} مشكلة جودة معروضة`}
      />

      <div className="p-6 space-y-4">
        {/* Dimension filter */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setDim("")}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors ${
              dim === ""
                ? "border-blue-500 bg-blue-50 text-blue-800"
                : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
            }`}
          >
            الكل
          </button>
          {DIMENSIONS.map((d) => (
            <button
              key={d}
              onClick={() => setDim(d)}
              className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors ${
                dim === d
                  ? "border-blue-500 bg-blue-50 text-blue-800"
                  : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50"
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  {[
                    "الملف",
                    "رقم الصف",
                    "العمود",
                    "بُعد الجودة",
                    "نوع العيب",
                    "الوصف",
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
                {isLoading
                  ? Array.from({ length: 10 }).map((_, i) => (
                      <tr key={i} className="border-b border-gray-50">
                        {Array.from({ length: 6 }).map((_, j) => (
                          <td key={j} className="px-4 py-3">
                            <div className="h-4 animate-pulse rounded bg-gray-100" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : !data?.length
                  ? (
                    <tr>
                      <td
                        colSpan={6}
                        className="py-16 text-center text-sm text-gray-400"
                      >
                        لا توجد مشاكل جودة — شغّل خط المعالجة أولاً
                      </td>
                    </tr>
                  )
                  : data.map((f, i) => (
                      <tr
                        key={i}
                        className="border-b border-gray-50 hover:bg-gray-50/50"
                      >
                        <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                          {f.file}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                          {f.row_id}
                        </td>
                        <td className="px-4 py-3 text-xs font-medium text-gray-700 font-mono">
                          {f.column}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              DIM_COLORS[f.dq_dimension] ??
                              "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {f.dq_dimension}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {f.defect_type}
                        </td>
                        <td className="px-4 py-3 max-w-[300px] text-xs text-gray-500 truncate">
                          {f.description}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
