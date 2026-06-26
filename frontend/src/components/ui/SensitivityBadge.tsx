import { cn, LEVEL_CONFIG } from "@/lib/utils";
import type { NdmoLevel } from "@/types";

interface Props {
  level: NdmoLevel;
  size?: "sm" | "md";
}

export function SensitivityBadge({ level, size = "md" }: Props) {
  const cfg = LEVEL_CONFIG[level];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border font-medium",
        cfg.bg,
        cfg.text,
        cfg.border,
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm"
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
      {level}
    </span>
  );
}
