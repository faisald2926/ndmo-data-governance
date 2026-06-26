"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchEvaluate } from "@/lib/api";
import { Topbar } from "@/components/layout/Topbar";
import { SensitivityBadge } from "@/components/ui/SensitivityBadge";
import { LEVELS } from "@/types";
import type { NdmoLevel } from "@/types";
import { formatPercent, cn } from "@/lib/utils";
import { BarChart2, Play } from "lucide-react";

export default function EvaluationPage() {
  const [enabled, setEnabled] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["evaluate"],
    queryFn: fetchEvaluate,
    enabled,
    retry: false,
  });

  function handleRun() {
    setEnabled(true);
    refetch();
  }

  const accuracy = data?.classification?.accuracy;
  const levels = (data?.classification?.levels ?? LEVELS) as NdmoLevel[];
  const cm = data?.classification?.confusion_matrix ?? {};
  const qualityByDim = data?.quality?.by_dimension ?? {};
  const qualityOverall = data?.quality?.overall;

  return (
    <div>
      <Topbar
        title="تقييم الأداء"
        subtitle="مقارنة نتائج التصنيف مع مفاتيح الإجابة"
      />

      <div className="p-6 space-y-6">
        {/* Run button */}
        {!enabled && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 gap-4">
            <BarChart2 className="h-10 w-10 text-gray-300" strokeWidth={1.5} />
            <p className="text-sm text-gray-500">
              اضغط لتشغيل التقييم على آخر نتائج خط المعالجة
            </p>
            <button
              onClick={handleRun}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-800 transition-colors"
            >
              <Play className="h-4 w-4" strokeWidth={1.75} />
              تشغيل التقييم
            </button>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-900 border-t-transparent" />
          </div>
        )}

        {isError && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
            تعذّر تشغيل التقييم — تأكد من وجود بيانات في قاعدة البيانات.
          </div>
        )}

        {data && (
          <>
            {/* Accuracy metric */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm text-center">
                <p className="text-xs text-gray-400 mb-1">دقة التصنيف</p>
                <p
                  className={cn(
                    "text-4xl font-bold",
                    accuracy != null && accuracy >= 0.8
                      ? "text-green-600"
                      : accuracy != null && accuracy >= 0.6
                      ? "text-amber-500"
                      : "text-red-500"
                  )}
                >
                  {accuracy != null ? formatPercent(accuracy) : "—"}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {data.classification.evaluated} سجل تم تقييمه
                </p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm text-center">
                <p className="text-xs text-gray-400 mb-1">دقة اكتشاف مشاكل الجودة</p>
                <p className="text-4xl font-bold text-blue-700">
                  {formatPercent(qualityOverall?.precision)}
                </p>
                <p className="text-xs text-gray-400 mt-1">Precision</p>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm text-center">
                <p className="text-xs text-gray-400 mb-1">نسبة الاسترجاع</p>
                <p className="text-4xl font-bold text-blue-700">
                  {formatPercent(qualityOverall?.recall)}
                </p>
                <p className="text-xs text-gray-400 mt-1">Recall</p>
              </div>
            </div>

            {/* Confusion matrix */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
                مصفوفة الالتباس (صحيح ↓ / متوقع →)
              </h2>
              <div className="overflow-x-auto">
                <table className="text-sm">
                  <thead>
                    <tr>
                      <th className="px-3 py-2 text-right text-xs text-gray-400">
                        الصحيح / المتوقع
                      </th>
                      {levels.map((l) => (
                        <th key={l} className="px-3 py-2 text-center min-w-[80px]">
                          <SensitivityBadge level={l} size="sm" />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {levels.map((rowLevel) => (
                      <tr key={rowLevel} className="border-t border-gray-50">
                        <td className="px-3 py-2">
                          <SensitivityBadge level={rowLevel} size="sm" />
                        </td>
                        {levels.map((colLevel) => {
                          const val =
                            cm[rowLevel]?.[colLevel] ?? 0;
                          const isDiag = rowLevel === colLevel;
                          return (
                            <td
                              key={colLevel}
                              className={cn(
                                "px-3 py-2 text-center text-sm font-medium rounded",
                                isDiag && val > 0
                                  ? "bg-green-50 text-green-700"
                                  : val > 0
                                  ? "bg-red-50 text-red-600"
                                  : "text-gray-300"
                              )}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Quality by dimension */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
                جودة البيانات: الدقة والاسترجاع حسب البُعد
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50">
                      {["البُعد", "Precision", "Recall"].map((h) => (
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
                    {Object.entries(qualityByDim).map(([dim, scores]) => (
                      <tr
                        key={dim}
                        className="border-b border-gray-50 hover:bg-gray-50/50"
                      >
                        <td className="px-4 py-3 font-medium text-gray-700">
                          {dim}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {formatPercent(scores.precision)}
                        </td>
                        <td className="px-4 py-3 text-gray-600">
                          {formatPercent(scores.recall)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
