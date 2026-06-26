"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchLineage } from "@/lib/api";
import { Topbar } from "@/components/layout/Topbar";
import { SensitivityBadge } from "@/components/ui/SensitivityBadge";
import { LEVEL_COLORS } from "@/lib/utils";
import type { NdmoLevel } from "@/types";
import { GitBranch } from "lucide-react";

export default function LineagePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["lineage"],
    queryFn: fetchLineage,
  });

  const nodes = data?.graph?.nodes ?? [];
  const edges = data?.graph?.edges ?? [];
  const events = data?.events ?? [];

  // Build a simple SVG-based DAG layout (left to right)
  const nodeMap = new Map<string, { x: number; y: number; level?: NdmoLevel }>();
  const COLS = 3;
  nodes.forEach((n, i) => {
    nodeMap.set(n.id, {
      x: (i % COLS) * 260 + 60,
      y: Math.floor(i / COLS) * 110 + 50,
      level: n.level as NdmoLevel | undefined,
    });
  });

  const svgW = Math.max(700, COLS * 260 + 100);
  const svgH = Math.max(300, Math.ceil(nodes.length / COLS) * 110 + 80);

  return (
    <div>
      <Topbar
        title="أثر البيانات (Data Lineage)"
        subtitle="تتبع مسار البيانات من المصدر إلى التقارير"
      />

      <div className="p-6 space-y-6">
        {isLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-900 border-t-transparent" />
          </div>
        )}

        {!isLoading && nodes.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-white py-16 gap-3">
            <GitBranch className="h-10 w-10 text-gray-300" strokeWidth={1.5} />
            <p className="text-sm text-gray-400">
              لا توجد بيانات أثر — شغّل خط المعالجة أولاً
            </p>
          </div>
        )}

        {nodes.length > 0 && (
          <>
            {/* SVG Graph */}
            <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-gray-700" dir="rtl">
                مخطط تدفق البيانات
              </h2>
              <svg
                width={svgW}
                height={svgH}
                className="overflow-visible"
                style={{ minWidth: svgW }}
              >
                {/* Edges */}
                {edges.map((e, i) => {
                  const from = nodeMap.get(e.from);
                  const to = nodeMap.get(e.to);
                  if (!from || !to) return null;
                  const mx = (from.x + 120 + to.x) / 2;
                  return (
                    <g key={i}>
                      <path
                        d={`M${from.x + 120},${from.y + 24} C${mx},${from.y + 24} ${mx},${to.y + 24} ${to.x},${to.y + 24}`}
                        fill="none"
                        stroke="#d1d5db"
                        strokeWidth={2}
                        markerEnd="url(#arrow)"
                      />
                    </g>
                  );
                })}

                {/* Arrow marker */}
                <defs>
                  <marker
                    id="arrow"
                    markerWidth="8"
                    markerHeight="8"
                    refX="6"
                    refY="3"
                    orient="auto"
                  >
                    <path d="M0,0 L0,6 L8,3 z" fill="#9ca3af" />
                  </marker>
                </defs>

                {/* Nodes */}
                {nodes.map((n) => {
                  const pos = nodeMap.get(n.id);
                  if (!pos) return null;
                  const color = pos.level
                    ? LEVEL_COLORS[pos.level] ?? "#6b7280"
                    : "#6b7280";
                  return (
                    <g key={n.id} transform={`translate(${pos.x},${pos.y})`}>
                      <rect
                        width={120}
                        height={48}
                        rx={8}
                        fill="white"
                        stroke={color}
                        strokeWidth={1.5}
                      />
                      <text
                        x={60}
                        y={18}
                        textAnchor="middle"
                        fontSize={11}
                        fontWeight={500}
                        fill="#111827"
                        fontFamily="inherit"
                      >
                        {n.id.length > 14 ? n.id.slice(0, 14) + "…" : n.id}
                      </text>
                      {pos.level && (
                        <text
                          x={60}
                          y={34}
                          textAnchor="middle"
                          fontSize={10}
                          fill={color}
                          fontFamily="inherit"
                        >
                          [{pos.level}]
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Events list */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-gray-700" dir="rtl">
                أحداث الأثر
              </h2>
              <div className="space-y-2">
                {events.map((ev, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-lg bg-gray-50 px-4 py-3"
                    dir="rtl"
                  >
                    <SensitivityBadge
                      level={ev.derived_level}
                      size="sm"
                    />
                    <span className="font-mono text-xs text-gray-700 font-medium">
                      {ev.job}
                    </span>
                    {ev.note && (
                      <span className="text-xs text-gray-400">{ev.note}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
