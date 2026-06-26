"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { runPipeline } from "@/lib/api";
import { Topbar } from "@/components/layout/Topbar";
import { Play, CheckCircle2, AlertTriangle } from "lucide-react";

const STEPS = [
  { label: "استيراد البيانات (Ingest)", key: "ingest" },
  { label: "تصنيف السجلات (Classify)", key: "classify" },
  { label: "فحص الجودة (Quality)", key: "quality" },
  { label: "تتبع الأثر (Lineage)", key: "lineage" },
];

export default function PipelinePage() {
  const [maxRows, setMaxRows] = useState(300);
  const [activeStep, setActiveStep] = useState(-1);

  const mutation = useMutation({
    mutationFn: () => runPipeline(maxRows || undefined),
    onMutate: () => setActiveStep(0),
    onSuccess: () => setActiveStep(4),
    onError: () => setActiveStep(-1),
  });

  // Simulate step progress during the long pipeline call
  useState(() => {
    if (!mutation.isPending) return;
    const timers = STEPS.map((_, i) =>
      setTimeout(() => setActiveStep(i + 1), i * 8000)
    );
    return () => timers.forEach(clearTimeout);
  });

  return (
    <div>
      <Topbar
        title="خط المعالجة"
        subtitle="استيراد → تصنيف → جودة → أثر"
      />

      <div className="p-6 max-w-2xl space-y-6">
        {/* Config */}
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm space-y-5">
          <h2 className="text-sm font-semibold text-gray-700" dir="rtl">
            إعدادات التشغيل
          </h2>

          <div className="flex items-center gap-4" dir="rtl">
            <label className="text-sm text-gray-600 min-w-[180px]">
              الحد الأقصى للصفوف لكل ملف
            </label>
            <input
              type="number"
              min={0}
              max={20000}
              step={100}
              value={maxRows}
              onChange={(e) => setMaxRows(Number(e.target.value))}
              className="w-32 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={mutation.isPending}
            />
            <span className="text-xs text-gray-400">
              (0 = كل الصفوف)
            </span>
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Play className="h-4 w-4" strokeWidth={1.75} />
            {mutation.isPending ? "جارٍ التشغيل…" : "▶ تشغيل خط المعالجة"}
          </button>
        </div>

        {/* Progress steps */}
        {(mutation.isPending || mutation.isSuccess || mutation.isError) && (
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
              حالة التشغيل
            </h2>
            <ol className="space-y-3">
              {STEPS.map((step, i) => {
                const done = mutation.isSuccess || activeStep > i + 1;
                const active = mutation.isPending && activeStep === i + 1;
                const waiting = activeStep <= i && !mutation.isSuccess;
                return (
                  <li
                    key={step.key}
                    className="flex items-center gap-3"
                    dir="rtl"
                  >
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border text-xs font-medium">
                      {done ? (
                        <CheckCircle2
                          className="h-5 w-5 text-green-500"
                          strokeWidth={2}
                        />
                      ) : active ? (
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-900 border-t-transparent" />
                      ) : (
                        <span className="text-gray-400">{i + 1}</span>
                      )}
                    </div>
                    <span
                      className={
                        done
                          ? "text-sm text-green-700 font-medium"
                          : active
                          ? "text-sm text-blue-900 font-medium"
                          : waiting
                          ? "text-sm text-gray-400"
                          : "text-sm text-gray-400"
                      }
                    >
                      {step.label}
                    </span>
                  </li>
                );
              })}
            </ol>

            {mutation.isSuccess && mutation.data && (
              <div className="mt-4 rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800" dir="rtl">
                <CheckCircle2
                  className="inline h-4 w-4 mr-1.5 mb-0.5"
                  strokeWidth={2}
                />
                اكتمل بنجاح ·{" "}
                <strong>{mutation.data.quality_findings}</strong> مشكلة جودة
                تم اكتشافها
              </div>
            )}

            {mutation.isError && (
              <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center gap-2" dir="rtl">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" strokeWidth={1.75} />
                فشل التشغيل — تحقق من اتصال الـ API وسجلات الخادم
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
