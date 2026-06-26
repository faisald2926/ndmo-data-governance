// ── Sensitivity levels (NDMO policy, ordered low → high) ────────────────────
export const LEVELS = ["عام", "مقيّد", "سري", "سري للغاية"] as const;
export type NdmoLevel = (typeof LEVELS)[number];

export const DIMENSIONS = [
  "Completeness",
  "Uniqueness",
  "Timeliness",
  "Validity",
  "Accuracy",
  "Consistency",
] as const;
export type DqDimension = (typeof DIMENSIONS)[number];

// ── RBAC ─────────────────────────────────────────────────────────────────────
export const ROLES = ["admin", "reviewer", "analyst", "viewer"] as const;
export type Role = (typeof ROLES)[number];

// Level access per role (minimum level visible)
export const ROLE_LEVEL_ACCESS: Record<Role, NdmoLevel[]> = {
  admin:    ["عام", "مقيّد", "سري", "سري للغاية"],
  reviewer: ["عام", "مقيّد", "سري"],
  analyst:  ["عام", "مقيّد"],
  viewer:   ["عام"],
};

// ── API response shapes ───────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  llm_mode: string;
  model: string;
}

export interface StatsResponse {
  total_records: number;
  classified: number;
  needs_review: number;
  classification_by_level: Partial<Record<NdmoLevel, number>>;
  quality_findings_by_dimension: Partial<Record<DqDimension, number>>;
}

export interface ClassificationRecord {
  source_file: string;
  record_id: string;
  ndmo_level: NdmoLevel;
  impact_category: string;
  confidence: number;
  decided_by: string;
  evidence: string;
  rationale: string;
  needs_review: boolean;
  control_recommendation: string;
}

export interface QualityFinding {
  file: string;
  row_id: string;
  column: string;
  dq_dimension: DqDimension;
  defect_type: string;
  description: string;
}

export interface LineageNode {
  id: string;
  level?: NdmoLevel;
}

export interface LineageEdge {
  from: string;
  to: string;
}

export interface LineageEvent {
  job: string;
  derived_level: NdmoLevel;
  note?: string;
}

export interface LineageResponse {
  graph: { nodes: LineageNode[]; edges: LineageEdge[] };
  events: LineageEvent[];
}

export interface ClassifyRequest {
  text?: string;
  content?: Record<string, unknown>;
}

export interface ClassifyResponse {
  ndmo_level: NdmoLevel;
  confidence: number;
  needs_review: boolean;
  decided_by: string;
  evidence?: string;
  rationale?: string;
  pii_types?: string[];
  control_recommendation?: string;
}

export interface EvaluateResponse {
  classification: {
    accuracy: number | null;
    evaluated: number;
    levels: NdmoLevel[];
    confusion_matrix: Record<string, Record<string, number>>;
  };
  quality: {
    overall: { precision: number; recall: number };
    by_dimension: Record<string, { precision: number; recall: number }>;
  };
}

export interface PipelineRunResponse {
  quality_findings: number;
  [key: string]: unknown;
}

// ── Auth / session ────────────────────────────────────────────────────────────
export interface User {
  id: string;
  username: string;
  role: Role;
  display_name: string;
}

export interface AuthSession {
  user: User;
  token: string;
}
