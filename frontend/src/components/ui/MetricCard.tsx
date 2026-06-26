import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  icon: LucideIcon;
  iconColor?: string;
  subtitle?: string;
  highlight?: boolean;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  iconColor = "text-blue-600",
  subtitle,
  highlight,
}: Props) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-white p-5 shadow-sm",
        highlight && "border-amber-300 bg-amber-50"
      )}
    >
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <div className={cn("rounded-lg p-2 bg-gray-50", highlight && "bg-white")}>
          <Icon className={cn("h-5 w-5", iconColor)} strokeWidth={1.75} />
        </div>
      </div>
      <p className="mt-3 text-3xl font-semibold text-gray-900">{value}</p>
      {subtitle && (
        <p className="mt-1 text-xs text-gray-400">{subtitle}</p>
      )}
    </div>
  );
}
