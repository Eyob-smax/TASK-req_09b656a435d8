import { request } from '@/services/http'

export interface FeatureFlag {
  id: string
  key: string
  value: string
  value_type: string
  description: string | null
  updated_by: string | null
  updated_at: string
}

export interface CohortDefinition {
  id: string
  cohort_key: string
  name: string
  description: string | null
  flag_overrides: Record<string, string> | null
  is_active: boolean
  created_at: string
}

export interface BootstrapConfig {
  user_id: string
  role: string
  cohort_key: string | null
  feature_flags: Record<string, string>
  flag_overrides: Record<string, string>
  resolved_flags: Record<string, string>
  issued_at: string
  signature: string
}

export interface ExportJob {
  id: string
  requested_by: string
  export_type: string
  status: string
  sha256_hash: string | null
  watermark_applied: boolean
  completed_at: string | null
  created_at: string
}

export interface ForecastSnapshot {
  id: string
  computed_at: string
  forecast_horizon_days: number
  request_volume_forecast: Record<string, number>
  bandwidth_p50_bytes: number | null
  bandwidth_p95_bytes: number | null
  upload_volume_trend: Record<string, unknown> | null
  input_window_days: number
}

export interface CacheHitStat {
  id: string
  window_start: string
  window_end: string
  asset_group: string
  total_requests: number
  cache_hits: number
  cache_misses: number
  hit_rate_pct: number | null
  computed_at: string
}

export interface AuditEntry {
  id: string
  event_type: string
  actor_id: string | null
  actor_role: string | null
  resource_type: string | null
  resource_id: string | null
  occurred_at: string
  trace_id: string | null
  outcome: string
  detail: Record<string, unknown> | null
}

export interface RbacPolicy {
  roles: string[]
  download_approved_roles: string[]
  privileged_roles: string[]
  route_restrictions: Record<string, string[]>
}

export interface MaskingPolicy {
  masked_fields: Record<string, { mask: string; visible_to: string[] }>
  restricted_downloads: Record<string, { allowed_roles: string[]; watermark_applied: boolean }>
}

export async function getFlags(): Promise<FeatureFlag[]> {
  return request<FeatureFlag[]>({ method: 'GET', path: '/api/v1/admin/feature-flags' })
}

export async function updateFlag(
  key: string,
  value: string,
  change_reason?: string,
): Promise<FeatureFlag> {
  return request<FeatureFlag>({
    method: 'PATCH',
    path: `/api/v1/admin/feature-flags/${encodeURIComponent(key)}`,
    body: { value, change_reason: change_reason ?? null },
  })
}

export async function listCohorts(): Promise<CohortDefinition[]> {
  return request<CohortDefinition[]>({ method: 'GET', path: '/api/v1/admin/cohorts' })
}

export async function createCohort(
  cohort_key: string,
  name: string,
  flag_overrides?: Record<string, string>,
): Promise<CohortDefinition> {
  return request<CohortDefinition>({
    method: 'POST',
    path: '/api/v1/admin/cohorts',
    body: { cohort_key, name, flag_overrides: flag_overrides ?? null },
  })
}

export async function assignCohort(cohort_id: string, user_id: string): Promise<unknown> {
  return request({ method: 'POST', path: `/api/v1/admin/cohorts/${cohort_id}/assign`, body: { user_id } })
}

export async function getBootstrapConfig(user_id: string): Promise<BootstrapConfig> {
  return request<BootstrapConfig>({ method: 'GET', path: `/api/v1/admin/config/bootstrap/${user_id}` })
}

export async function searchAudit(params: {
  event_type?: string
  actor_id?: string
  resource_type?: string
  outcome?: string
  from_date?: string
  to_date?: string
  page?: number
  page_size?: number
}): Promise<{ data: AuditEntry[]; pagination: { total: number; page: number; page_size: number; total_pages: number } }> {
  const qs = new URLSearchParams()
  if (params.event_type) qs.set('event_type', params.event_type)
  if (params.actor_id) qs.set('actor_id', params.actor_id)
  if (params.resource_type) qs.set('resource_type', params.resource_type)
  if (params.outcome) qs.set('outcome', params.outcome)
  if (params.from_date) qs.set('from_date', params.from_date)
  if (params.to_date) qs.set('to_date', params.to_date)
  if (params.page) qs.set('page', String(params.page))
  if (params.page_size) qs.set('page_size', String(params.page_size))
  const query = qs.toString() ? `?${qs}` : ''
  const raw = await fetch(`/api/v1/admin/audit${query}`, {
    headers: { Authorization: `Bearer ${_getToken()}` },
  })
  const json = await raw.json()
  return { data: json.data, pagination: json.pagination }
}

export async function getRbacPolicy(): Promise<RbacPolicy> {
  return request<RbacPolicy>({ method: 'GET', path: '/api/v1/admin/rbac-policy' })
}

export async function getMaskingPolicy(): Promise<MaskingPolicy> {
  return request<MaskingPolicy>({ method: 'GET', path: '/api/v1/admin/masking-policy' })
}

export async function getMetricsSummary(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>({ method: 'GET', path: '/api/v1/admin/metrics/summary' })
}

export async function listForecasts(page = 1): Promise<{ data: ForecastSnapshot[]; pagination: { total: number } }> {
  const raw = await fetch(`/api/v1/admin/forecasts?page=${page}`, {
    headers: { Authorization: `Bearer ${_getToken()}` },
  })
  const json = await raw.json()
  return { data: json.data, pagination: json.pagination }
}

export async function triggerForecast(horizon_days = 30, input_window_days = 90): Promise<ForecastSnapshot> {
  return request<ForecastSnapshot>({
    method: 'POST',
    path: `/api/v1/admin/forecasts/compute?horizon_days=${horizon_days}&input_window_days=${input_window_days}`,
  })
}

export async function listCacheStats(page = 1): Promise<{ data: CacheHitStat[]; pagination: { total: number } }> {
  const raw = await fetch(`/api/v1/admin/cache-stats?page=${page}`, {
    headers: { Authorization: `Bearer ${_getToken()}` },
  })
  const json = await raw.json()
  return { data: json.data, pagination: json.pagination }
}

export async function createExport(export_type: string, filters?: Record<string, unknown>): Promise<ExportJob> {
  return request<ExportJob>({
    method: 'POST',
    path: '/api/v1/admin/exports',
    body: { export_type, filters: filters ?? null },
  })
}

export async function listExports(page = 1): Promise<{ data: ExportJob[]; pagination: { total: number } }> {
  const raw = await fetch(`/api/v1/admin/exports?page=${page}`, {
    headers: { Authorization: `Bearer ${_getToken()}` },
  })
  const json = await raw.json()
  return { data: json.data, pagination: json.pagination }
}

function _getToken(): string {
  try {
    const raw = localStorage.getItem('auth')
    if (!raw) return ''
    return JSON.parse(raw).access_token ?? ''
  } catch {
    return ''
  }
}
