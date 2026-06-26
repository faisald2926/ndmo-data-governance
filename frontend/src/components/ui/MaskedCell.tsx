import { cn } from "@/lib/utils";
import { maskField } from "@/lib/rbac";
import type { Role, NdmoLevel } from "@/types";

interface Props {
  value: string;
  column: string;
  role: Role;
  level: NdmoLevel;
}

export function MaskedCell({ value, column, role, level }: Props) {
  // Top-secret rows are hidden entirely at the row level, but guard here too
  if (level === "سري للغاية" && (role === "analyst" || role === "viewer")) {
    return <span className="text-gray-300 select-none">— محظور —</span>;
  }

  const masked = maskField(value, column, role);
  const isRedacted = masked !== value;

  return (
    <span
      className={cn(
        isRedacted && "font-mono tracking-widest text-gray-400 select-none"
      )}
    >
      {masked}
    </span>
  );
}
