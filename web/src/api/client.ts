/**
 * Dataclaw API 客户端
 */

const BASE_URL = '/api/v1'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Assets
  listAssets: () => request<Asset[]>('/assets'),
  getAsset: (name: string) => request<Asset>(`/assets/${name}`),
  listVersions: (name: string) => request<AssetVersion[]>(`/assets/${name}/versions`),

  // Ingest
  ingest: (data: IngestRequest) =>
    request<Asset>('/ingest', { method: 'POST', body: JSON.stringify(data) }),

  // Inspect
  inspect: (data: InspectRequest) =>
    request<InspectionReport>('/inspect', { method: 'POST', body: JSON.stringify(data) }),

  // Run
  run: (data: RunRequest) =>
    request<ExecutionRun>('/run', { method: 'POST', body: JSON.stringify(data) }),
  listRuns: () => request<ExecutionRun[]>('/runs'),

  // Diff
  diff: (data: DiffRequest) =>
    request<DiffResult>('/diff', { method: 'POST', body: JSON.stringify(data) }),

  // Publish
  publish: (data: PublishRequest) =>
    request<Publication>('/publish', { method: 'POST', body: JSON.stringify(data) }),
  listPublications: () => request<Publication[]>('/publications'),

  // Health
  health: () => request<{ status: string }>('/health'),
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface Asset {
  id: string
  name: string
  description: string | null
  asset_type: string
  status: string
  source_material_id: string | null
  created_at: string
  updated_at: string
}

export interface AssetVersion {
  id: string
  asset_id: string
  version_number: number
  status: string
  record_count: number | null
  storage_uri: string | null
  quality_metrics: Record<string, any> | null
  inspection_report: Record<string, any> | null
  created_at: string
}

export interface IngestRequest {
  source_uri: string
  name: string
  source_type?: string
  metadata?: Record<string, any>
}

export interface InspectRequest {
  asset_name: string
  version?: number | null
  focus?: string | null
}

export interface InspectionReport {
  asset: string
  version: string
  status: string
  record_count: number | null
  quality_metrics: Record<string, any>
  problems: ProblemCluster[]
  agent_analysis: string | null
}

export interface ProblemCluster {
  cluster_key: string
  label: string
  severity: 'high' | 'medium' | 'low'
  affected_count: number
  affected_ratio: number | null
  root_cause: string | null
  recommendation: string | null
}

export interface RunRequest {
  asset_name: string
  strategy_id: string
  clusters?: string[] | null
  confirm?: boolean
  parameters?: Record<string, any>
}

export interface ExecutionRun {
  id: string
  asset_id: string
  input_version_id: string
  strategy_id: string
  status: string
  execution_plan: Record<string, any> | null
  step_logs: Array<Record<string, any>> | null
  verification_results: Record<string, any> | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  created_at: string
}

export interface DiffRequest {
  asset_name: string
  version_a: number
  version_b: number
}

export interface DiffResult {
  asset_name: string
  version_a: number
  version_b: number
  metrics_diff: Record<string, { a: any; b: any; delta: any }>
  cluster_changes: Array<{
    cluster_key: string
    status: 'changed' | 'resolved' | 'new'
    count_a: number
    count_b: number
  }>
  interpretation: string | null
}

export interface PublishRequest {
  asset_name: string
  version: number
  target: string
  publication_type?: string
  output_format?: string | null
  replaces?: string | null
  note?: string | null
}

export interface Publication {
  id: string
  asset_version_id: string
  publication_type: string
  target: string
  output_uri: string | null
  output_format: string | null
  gates_passed: Array<Record<string, any>> | null
  retained_risks: string[] | null
  note: string | null
  published_by: string | null
  published_at: string
}
