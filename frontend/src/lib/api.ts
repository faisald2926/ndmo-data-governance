import axios from "axios";
import type {
  HealthResponse,
  StatsResponse,
  ClassificationRecord,
  QualityFinding,
  LineageResponse,
  ClassifyRequest,
  ClassifyResponse,
  EvaluateResponse,
  PipelineRunResponse,
  NdmoLevel,
  DqDimension,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const http = axios.create({ baseURL: BASE, timeout: 120_000 });

// Attach auth token from localStorage on every request
http.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ndmo_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Endpoints ────────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await http.get<HealthResponse>("/health");
  return data;
}

export async function fetchStats(): Promise<StatsResponse> {
  const { data } = await http.get<StatsResponse>("/stats");
  return data;
}

export async function fetchRecords(params: {
  level?: NdmoLevel;
  source_file?: string;
  limit?: number;
  offset?: number;
}): Promise<ClassificationRecord[]> {
  const { data } = await http.get<ClassificationRecord[]>("/records", {
    params,
    timeout: 30_000,
  });
  return data;
}

export async function fetchQualityFindings(params: {
  dimension?: DqDimension;
  source_file?: string;
  limit?: number;
}): Promise<QualityFinding[]> {
  const { data } = await http.get<QualityFinding[]>("/quality/findings", {
    params,
    timeout: 30_000,
  });
  return data;
}

export async function fetchLineage(): Promise<LineageResponse> {
  const { data } = await http.get<LineageResponse>("/lineage");
  return data;
}

export async function fetchEvaluate(): Promise<EvaluateResponse> {
  const { data } = await http.get<EvaluateResponse>("/evaluate", {
    timeout: 60_000,
  });
  return data;
}

export async function classify(req: ClassifyRequest): Promise<ClassifyResponse> {
  const { data } = await http.post<ClassifyResponse>("/classify", req, {
    timeout: 1_800_000,
  });
  return data;
}

export async function runPipeline(maxPerFile?: number): Promise<PipelineRunResponse> {
  const { data } = await http.post<PipelineRunResponse>(
    "/pipeline/run",
    { max_per_file: maxPerFile ?? null },
    { timeout: 1_800_000 }
  );
  return data;
}
