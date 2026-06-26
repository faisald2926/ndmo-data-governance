import type { NdmoLevel, Role } from "@/types";
import { ROLE_LEVEL_ACCESS } from "@/types";

// ── Level visibility ──────────────────────────────────────────────────────────
export function canSeeLevel(role: Role, level: NdmoLevel): boolean {
  return ROLE_LEVEL_ACCESS[role].includes(level);
}

// ── Data masking ──────────────────────────────────────────────────────────────
const MASK = "●●●●●●●";

/**
 * Mask a Saudi National ID (10-digit number starting with 1 or 2).
 * Admins and reviewers see the full value; analysts see last-3 only;
 * viewers see fully masked.
 */
export function maskNationalId(value: string, role: Role): string {
  if (!value) return value;
  if (role === "admin" || role === "reviewer") return value;
  if (role === "analyst") return `${MASK}${value.slice(-3)}`;
  return MASK;
}

/**
 * Mask an IBAN (SA…).
 */
export function maskIban(value: string, role: Role): string {
  if (!value) return value;
  if (role === "admin" || role === "reviewer") return value;
  if (role === "analyst") return `SA${MASK}${value.slice(-4)}`;
  return MASK;
}

/**
 * Mask a phone number.
 */
export function maskPhone(value: string, role: Role): string {
  if (!value) return value;
  if (role === "admin" || role === "reviewer") return value;
  return `+966${MASK}`;
}

/**
 * Generic field masker — auto-detects what kind of PII it is by column name.
 */
export function maskField(
  value: string,
  columnName: string,
  role: Role
): string {
  const col = columnName.toLowerCase();
  if (col.includes("national_id") || col.includes("id_number"))
    return maskNationalId(value, role);
  if (col.includes("iban")) return maskIban(value, role);
  if (col.includes("mobile") || col.includes("phone"))
    return maskPhone(value, role);
  return value;
}

// ── Route permissions ─────────────────────────────────────────────────────────
export const ROUTE_ROLES: Record<string, Role[]> = {
  "/dashboard":   ["admin", "reviewer", "analyst", "viewer"],
  "/records":     ["admin", "reviewer", "analyst", "viewer"],
  "/quality":     ["admin", "reviewer", "analyst", "viewer"],
  "/evaluation":  ["admin", "reviewer"],
  "/lineage":     ["admin", "reviewer"],
  "/classify":    ["admin", "reviewer", "analyst"],
  "/pipeline":    ["admin"],
  "/audit-log":   ["admin"],
};

export function canAccessRoute(role: Role, path: string): boolean {
  const allowed = ROUTE_ROLES[path];
  if (!allowed) return false;
  return allowed.includes(role);
}
