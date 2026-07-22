const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export interface HealthStatus {
  status: string;
  llm_configured: boolean;
  embedding_backend: string;
}

export interface DashboardStats {
  total_documents: number;
  total_equipment: number;
  total_incidents: number;
  open_high_risk_equipment: number;
  compliance_score_avg: number;
  docs_by_category: Record<string, number>;
  failure_trend: { month: string; failures: number }[];
}

export interface DocumentOut {
  id: string;
  filename: string;
  file_type: string;
  upload_date: string;
  plant?: string | null;
  department?: string | null;
  engineer?: string | null;
  doc_category?: string | null;
  risk_level?: string | null;
}

export interface Citation {
  document_id: string;
  filename: string;
  snippet: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  related_entities: string[];
}

export interface RootCauseStage {
  stage: string;
  evidence: string;
  source_document_id?: string | null;
  source_filename?: string | null;
}

export interface RootCauseResponse {
  equipment_name: string | null;
  chain: RootCauseStage[];
  summary: string;
  confidence: number;
}

export interface MaintenanceResponse {
  equipment_name: string;
  risk_score: number;
  risk_level: string;
  days_since_last_maintenance: number | null;
  failure_count_last_year: number;
  recommendation: string;
  recommended_next_date: string | null;
}

export interface ComplianceRuleResult {
  rule: string;
  standard: string;
  passed: boolean;
  explanation: string;
}

export interface ComplianceResponse {
  document_id: string;
  filename: string;
  results: ComplianceRuleResult[];
  compliance_score: number;
}

export interface EntityOut {
  id: string;
  name: string;
  entity_type: string;
  attributes: Record<string, unknown>;
}

export interface RelationshipOut {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relation_type: string;
  confidence: number;
}

export interface EntityGraph {
  entity: EntityOut;
  relationships: RelationshipOut[];
  neighbors: EntityOut[];
}

export interface SearchResult {
  query: string;
  mode: string;
  semantic_results: { type: string; document_id: string; filename: string; snippet: string; score: number | null }[];
  keyword_results: { type: string; document_id: string; filename: string; snippet: string }[];
  entity_results: { type: string; entity_id: string; name: string; entity_type: string }[];
}

export const api = {
  health: () => request<HealthStatus>("/api/health"),
  dashboardStats: () => request<DashboardStats>("/api/dashboard/stats"),
  listDocuments: (params?: { plant?: string; doc_category?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<DocumentOut[]>(`/api/documents${qs ? `?${qs}` : ""}`);
  },
  ingestDocument: async (file: File, meta: Record<string, string>) => {
    const form = new FormData();
    form.append("file", file);
    Object.entries(meta).forEach(([k, v]) => v && form.append(k, v));
    const res = await fetch(`${API_BASE}/api/ingest`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json() as Promise<DocumentOut>;
  },
  search: (q: string, mode: "semantic" | "keyword" | "hybrid" = "hybrid") =>
    request<SearchResult>(`/api/search?q=${encodeURIComponent(q)}&mode=${mode}`),
  chat: (query: string, history: unknown[] = []) =>
    request<ChatResponse>("/api/chat", { method: "POST", body: JSON.stringify({ query, history }) }),
  rootCause: (equipment_name?: string, failure_description?: string) =>
    request<RootCauseResponse>("/api/agents/root-cause", {
      method: "POST",
      body: JSON.stringify({ equipment_name, failure_description }),
    }),
  maintenance: (equipment_name: string) =>
    request<MaintenanceResponse>("/api/agents/maintenance", {
      method: "POST",
      body: JSON.stringify({ equipment_name }),
    }),
  compliance: (document_id: string) =>
    request<ComplianceResponse>("/api/agents/compliance", {
      method: "POST",
      body: JSON.stringify({ document_id }),
    }),
  graphSearch: (name: string) => request<EntityOut[]>(`/api/graph/search?name=${encodeURIComponent(name)}`),
  graphEntity: (id: string) => request<EntityGraph>(`/api/graph/entity/${id}`),
};
