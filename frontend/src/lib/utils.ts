import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { NdmoLevel } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── Sensitivity level colour config ──────────────────────────────────────────
export const LEVEL_CONFIG: Record<
  NdmoLevel,
  { bg: string; text: string; border: string; dot: string; label: string }
> = {
  "سري للغاية": {
    bg: "bg-red-50",
    text: "text-red-800",
    border: "border-red-200",
    dot: "bg-red-500",
    label: "سري للغاية",
  },
  "سري": {
    bg: "bg-amber-50",
    text: "text-amber-800",
    border: "border-amber-200",
    dot: "bg-amber-500",
    label: "سري",
  },
  "مقيّد": {
    bg: "bg-blue-50",
    text: "text-blue-800",
    border: "border-blue-200",
    dot: "bg-blue-500",
    label: "مقيّد",
  },
  "عام": {
    bg: "bg-green-50",
    text: "text-green-800",
    border: "border-green-200",
    dot: "bg-green-500",
    label: "عام",
  },
};

export const LEVEL_COLORS: Record<NdmoLevel, string> = {
  "سري للغاية": "#E24B4A",
  "سري":        "#BA7517",
  "مقيّد":      "#185FA5",
  "عام":        "#3B6D11",
};

export function formatConfidence(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${Math.round(v * 100)}%`;
}

export function formatPercent(v: number | null | undefined): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}
