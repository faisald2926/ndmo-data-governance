"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { classify } from "@/lib/api";
import { Topbar } from "@/components/layout/Topbar";
import { SensitivityBadge } from "@/components/ui/SensitivityBadge";
import { formatConfidence } from "@/lib/utils";
import { Wand2, AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import type { ClassifyResponse } from "@/types";

const EXAMPLES = [
  "أعاني من حالة صحية وأطلب إعفاءً، هويتي 1043215789",
  "تقرير عدد السكان في المنطقة الوسطى للعام 2025",
  "رقم الحساب البنكي SA9159633362554118825523 للمورد",
  "خطط العمليات العسكرية للمنطقة الشمالية",
];

export default function ClassifyPage() {
  const [text, setText] = useState(EXAMPLES[0]);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [showRaw, setShowRaw] = useState(false);

  const mutation = useMutation({
    mutationFn: () => classify({ text }),
    onSuccess: (data) => setResult(data),
  });

  return (
    <div>
      <Topbar
        title="تصنيف مباشر"
        subtitle="جرّب التصنيف عبر الطبقات الثلاث: قواعد + نموذج + السياسة"
      />

      <div className="p-6 space-y-6 max-w-3xl">
        {/* Input */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-4">
          <label className="block text-sm font-medium text-gray-700" dir="rtl">
            النص المراد تصنيفه
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="w-full rounded-lg border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
            dir="rtl"
            placeholder="اكتب النص هنا…"
          />

          {/* Example chips */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs text-gray-400">أمثلة:</span>
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                onClick={() => setText(ex)}
                className="rounded-full border border-gray-200 px-2.5 py-0.5 text-xs text-gray-500 hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50 transition-colors truncate max-w-[200px]"
                dir="rtl"
                title={ex}
              >
                {ex.slice(0, 30)}…
              </button>
            ))}
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !text.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Wand2 className="h-4 w-4" strokeWidth={1.75} />
            {mutation.isPending ? "جارٍ التصنيف…" : "صنِّف"}
          </button>
        </div>

        {/* Loading */}
        {mutation.isPending && (
          <div className="flex items-center gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-700 border-t-transparent flex-shrink-0" />
            <span>يُعالج النموذج النص… قد يستغرق هذا لحظة</span>
          </div>
        )}

        {/* Error */}
        {mutation.isError && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" strokeWidth={1.75} />
            تعذّر التصنيف — تحقق من اتصال الـ API
          </div>
        )}

        {/* Result */}
        {result && !mutation.isPending && (
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-4">
            <h2 className="text-sm font-semibold text-gray-700" dir="rtl">
              نتيجة التصنيف
            </h2>

            {/* KPIs */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-400 mb-1.5">مستوى التصنيف</p>
                <SensitivityBadge level={result.ndmo_level} />
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-400 mb-1.5">الثقة</p>
                <p className="text-2xl font-bold text-gray-800">
                  {formatConfidence(result.confidence)}
                </p>
              </div>
              <div className="rounded-lg bg-gray-50 p-3 text-center">
                <p className="text-xs text-gray-400 mb-1.5">مراجعة بشرية</p>
                <p
                  className={`text-2xl font-bold ${
                    result.needs_review ? "text-amber-500" : "text-green-600"
                  }`}
                >
                  {result.needs_review ? "نعم" : "لا"}
                </p>
              </div>
            </div>

            {/* Details */}
            <div className="space-y-2 text-sm">
              <div className="flex gap-2 items-start" dir="rtl">
                <span className="text-gray-400 min-w-[110px]">قرار بواسطة:</span>
                <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded text-gray-700">
                  {result.decided_by}
                </span>
              </div>
              {result.evidence && (
                <div className="flex gap-2 items-start" dir="rtl">
                  <span className="text-gray-400 min-w-[110px]">الدليل:</span>
                  <span className="text-gray-700">{result.evidence}</span>
                </div>
              )}
              {result.pii_types && result.pii_types.length > 0 && (
                <div className="flex gap-2 items-start" dir="rtl">
                  <span className="text-gray-400 min-w-[110px]">أنواع PII:</span>
                  <div className="flex flex-wrap gap-1">
                    {result.pii_types.map((p) => (
                      <span
                        key={p}
                        className="rounded-full bg-red-50 border border-red-100 px-2 py-0.5 text-xs text-red-700"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {result.control_recommendation && (
                <div className="flex gap-2 items-start" dir="rtl">
                  <span className="text-gray-400 min-w-[110px]">التوصية:</span>
                  <span className="text-gray-600 text-xs">
                    {result.control_recommendation}
                  </span>
                </div>
              )}
            </div>

            {/* Raw JSON toggle */}
            <button
              onClick={() => setShowRaw((v) => !v)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              {showRaw ? (
                <ChevronUp className="h-3 w-3" strokeWidth={2} />
              ) : (
                <ChevronDown className="h-3 w-3" strokeWidth={2} />
              )}
              {showRaw ? "إخفاء JSON" : "عرض JSON الكامل"}
            </button>
            {showRaw && (
              <pre className="overflow-x-auto rounded-lg bg-gray-950 p-4 text-xs text-green-400 font-mono">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
