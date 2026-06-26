"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: Props) {
  const { data: health, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
    retry: false,
  });

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold text-gray-900" dir="rtl">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-gray-400" dir="rtl">
            {subtitle}
          </p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
            isError || !health
              ? "border-red-200 bg-red-50 text-red-700"
              : "border-green-200 bg-green-50 text-green-700"
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              isError || !health ? "bg-red-500" : "bg-green-500"
            )}
          />
          {health
            ? `API · ${health.llm_mode} · ${health.model}`
            : isError
            ? "API غير متاح"
            : "جارٍ الاتصال…"}
        </span>
      </div>
    </header>
  );
}
