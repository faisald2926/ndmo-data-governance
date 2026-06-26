"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Database,
  CheckCircle2,
  AlertTriangle,
  Bug,
} from "lucide-react";
import { fetchStats } from "@/lib/api";
import { MetricCard } from "@/components/ui/MetricCard";
import { Topbar } from "@/components/layout/Topbar";
import { LEVEL_COLORS } from "@/lib/utils";
import { LEVELS, DIMENSIONS } from "@/types";
import type { NdmoLevel } from "@/types";

export default function DashboardPage() {
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    refetchInterval: 30_000,
  });

  const levelData = LEVELS.map((l: NdmoLevel) => ({
    name: l,
    count: stats?.classification_by_level?.[l] ?? 0,
  }));

  const qualityData = Object.entries(stats?.quality_findings_by_dimension ?? {}).map(
    ([dim, count]) => ({ name: dim, count })
  );

  const totalQuality = Object.values(
    stats?.quality_findings_by_dimension ?? {}
  ).reduce((a, b) => a + b, 0);

  if (isError) {
    return (
      <div>
        <Topbar title="نظرة عامة" subtitle="لوحة التحكم الرئيسية" />
        <div className="flex flex-col items-center justify-center py-24 text-center px-6">
          <AlertTriangle className="h-10 w-10 text-amber-400 mb-3" strokeWidth={1.5} />
          <p className="text-gray-600 font-medium">تعذّر الاتصال بالـ API</p>
          <p className="text-sm text-gray-400 mt-1">
            تأكد من تشغيل خادم FastAPI على{" "}
            <code className="text-xs bg-gray-100 px-1 rounded">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Topbar title="نظرة عامة" subtitle="لوحة التحكم الرئيسية" />

      <div className="p-6 space-y-6">
        {/* KPI cards */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MetricCard
            title="إجمالي السجلات"
            value={isLoading ? "—" : (stats?.total_records ?? 0).toLocaleString()}
            icon={Database}
            iconColor="text-blue-600"
          />
          <MetricCard
            title="تم تصنيفها"
            value={isLoading ? "—" : (stats?.classified ?? 0).toLocaleString()}
            icon={CheckCircle2}
            iconColor="text-green-600"
            subtitle={
              stats
                ? `${Math.round((stats.classified / (stats.total_records || 1)) * 100)}% من الإجمالي`
                : undefined
            }
          />
          <MetricCard
            title="تحتاج مراجعة"
            value={isLoading ? "—" : (stats?.needs_review ?? 0).toLocaleString()}
            icon={AlertTriangle}
            iconColor="text-amber-500"
            highlight={(stats?.needs_review ?? 0) > 0}
          />
          <MetricCard
            title="مشاكل الجودة"
            value={isLoading ? "—" : totalQuality.toLocaleString()}
            icon={Bug}
            iconColor="text-red-500"
          />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Classification distribution */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
              توزيع مستويات التصنيف
            </h2>
            {isLoading ? (
              <div className="h-52 animate-pulse rounded-lg bg-gray-100" />
            ) : (
              <ResponsiveContainer width="100%" height={210}>
                <BarChart data={levelData} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 12, fill: "#6b7280" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#9ca3af" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    formatter={(v) => [v, "سجل"]}
                    labelStyle={{ fontFamily: "inherit", fontSize: 13 }}
                    contentStyle={{
                      border: "1px solid #e5e7eb",
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {levelData.map((entry: { name: string; count: number }) => (
                      <Cell
                        key={entry.name}
                        fill={LEVEL_COLORS[entry.name as NdmoLevel]}
                        fillOpacity={0.85}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Quality findings by dimension */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
              مشاكل الجودة حسب البُعد
            </h2>
            {isLoading ? (
              <div className="h-52 animate-pulse rounded-lg bg-gray-100" />
            ) : qualityData.length === 0 ? (
              <div className="flex h-52 items-center justify-center text-sm text-gray-400">
                لا توجد بيانات — شغّل خط المعالجة أولاً
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={210}>
                <BarChart data={qualityData} margin={{ top: 4, right: 0, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: "#6b7280" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#9ca3af" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      border: "1px solid #e5e7eb",
                      borderRadius: 8,
                      fontSize: 13,
                    }}
                  />
                  <Bar dataKey="count" fill="#185FA5" fillOpacity={0.8} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
