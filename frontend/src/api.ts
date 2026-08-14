const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

export type RunStatus = "queued" | "planning" | "discovering" | "fetching" | "extracting" | "comparing" | "synthesising" | "completed" | "partial" | "failed";

export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

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

// --- Enterprise Document RAG Types ---

export interface DocumentItem {
  id: string;
  project_id: string;
  filename: string;
  file_hash: string;
  file_size_bytes: number;
  status: DocumentStatus;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  page_number: number;
  chunk_index: number;
  raw_text: string;
  visual_summary: string | null;
  created_at: string;
}

export interface DocumentDetail extends DocumentItem {
  chunks: DocumentChunk[];
}

export interface DocumentList {
  documents: DocumentItem[];
  total: number;
}

export interface PageCitation {
  document_id: string;
  document_filename: string;
  page_number: number;
  chunk_index: number;
  verbatim_quote: string;
  score?: number | null;
}

export interface ReportSection {
  heading: string;
  content: string;
  confidence: "low" | "medium" | "high";
  citations: PageCitation[];
}

export interface RAGReport {
  id: string;
  project_id: string;
  question: string;
  summary: string;
  sections: ReportSection[];
  limitations: string;
  total_sources_cited: number;
  status: string;
  created_at: string;
}

export interface RAGReportList {
  reports: RAGReport[];
  total: number;
}

// --- HTTP Helpers ---

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

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "File upload failed.");
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

  // Document Management APIs
  uploadDocument: (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return uploadRequest<DocumentItem>(`/projects/${projectId}/documents`, formData);
  },
  projectDocuments: (projectId: string) => request<DocumentList>(`/projects/${projectId}/documents`),
  documentDetail: (documentId: string) => request<DocumentDetail>(`/documents/${documentId}`),
  deleteDocument: (documentId: string) => request<{ status: string; document_id: string }>(`/documents/${documentId}`, { method: "DELETE" }),

  // RAG Research APIs
  ragResearch: (projectId: string, question: string) =>
    request<RAGReport>(`/projects/${projectId}/rag-research`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  projectRAGReports: (projectId: string) => request<RAGReportList>(`/projects/${projectId}/rag-reports`),
  ragReport: (reportId: string) => request<RAGReport>(`/rag-reports/${reportId}`),
};
