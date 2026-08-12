const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export type RunStatus = "queued" | "planning" | "discovering" | "fetching" | "extracting" | "comparing" | "synthesising" | "completed" | "partial" | "failed";

export interface Run {
  id: string;
  project_id: string;
  status: RunStatus;
  provider_name: string;
  model_name: string;
  started_at: string | null;
  completed_at: string | null;
  error_summary: string | null;
  source_count: number;
  claim_count: number;
  conclusion_count: number;
}

export interface Conclusion {
  id: string;
  statement: string;
  confidence: string;
  reasoning?: string;
  limitations: string;
  claim_count: number;
}

export interface RunDetail extends Run {
  question: string;
  plan_items: string[];
  conclusions: Conclusion[];
}

export interface RunEvent {
  stage: string;
  status: string;
  message: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
}

export interface Source {
  id: string;
  title: string | null;
  canonical_url: string;
  publisher: string | null;
  source_type: string;
  retrieved_at: string | null;
  fetch_status: string | null;
}

export interface Claim {
  id: string;
  topic: string;
  statement: string;
  classification: string;
  confidence: string;
  exact_excerpt: string;
  source: Source;
}

export interface Assessment {
  id: string;
  left_claim_id: string;
  right_claim_id: string;
  relationship: "supports" | "qualifies" | "contradicts" | "unrelated";
  rationale: string;
  conditions: string;
  confidence: string;
}

export interface Trace {
  conclusion: Conclusion;
  claims: Claim[];
  assessments: Assessment[];
}

export interface Project {
  id: string;
  title: string;
  original_question: string;
  created_at: string;
  latest_run: Run | null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Request failed. Check the backend service.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; ai_provider?: string; model?: string; providers_configured: Record<string, boolean> }>("/health"),
  projects: () => request<Project[]>("/research-projects"),
  projectRuns: (projectId: string) => request<Run[]>(`/research-projects/${projectId}/runs`),
  createProject: (question: string) => request<{ project_id: string; run_id: string; status: RunStatus }>("/research-projects", { method: "POST", body: JSON.stringify({ question }) }),
  run: (id: string) => request<RunDetail>(`/research-runs/${id}`),
  events: (id: string) => request<RunEvent[]>(`/research-runs/${id}/events`),
  sources: (id: string) => request<Source[]>(`/research-runs/${id}/sources`),
  claims: (id: string) => request<Claim[]>(`/research-runs/${id}/claims`),
  assessments: (id: string) => request<Assessment[]>(`/research-runs/${id}/assessments`),
  trace: (id: string) => request<Trace>(`/conclusions/${id}/trace`),
  retry: (id: string) => request<Run>(`/research-runs/${id}/retry`, { method: "POST" }),
};
