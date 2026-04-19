import { addSigningHeaders, request } from './http'
import type {
  AttendanceAnomaly,
  AttendanceException,
  AnomalyCreate,
  AttendanceExceptionCreate,
  ReviewDecisionCreate,
  ProofUploadResponse,
  ExceptionReviewStep,
} from '@/types/attendance'
import type { Pagination } from '@/types'

export function flagAnomaly(data: AnomalyCreate): Promise<AttendanceAnomaly> {
  return request<AttendanceAnomaly>({
    method: 'POST',
    path: '/api/v1/attendance/anomalies',
    body: data,
  })
}

export function listAnomalies(candidateId?: string): Promise<AttendanceAnomaly[]> {
  const qs = candidateId ? `?candidate_id=${encodeURIComponent(candidateId)}` : ''
  return request<AttendanceAnomaly[]>({
    method: 'GET',
    path: `/api/v1/attendance/anomalies${qs}`,
  })
}

export function createException(
  data: AttendanceExceptionCreate,
): Promise<AttendanceException> {
  return request<AttendanceException>({
    method: 'POST',
    path: '/api/v1/attendance/exceptions',
    body: data,
  })
}

export async function listExceptions(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<{ data: AttendanceException[]; pagination: Pagination }> {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const qs = new URLSearchParams()
  if (params?.status) qs.set('status', params.status)
  if (params?.page) qs.set('page', String(params.page))
  if (params?.page_size) qs.set('page_size', String(params.page_size))
  const query = qs.toString() ? `?${qs}` : ''
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (auth.tokens?.access_token) headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  const r = await fetch(`/api/v1/attendance/exceptions${query}`, {
    method: 'GET',
    credentials: 'same-origin',
    headers,
  })
  const body = await r.json()
  if (!r.ok) throw new Error(body?.error?.message ?? `HTTP ${r.status}`)
  return { data: body.data, pagination: body.pagination }
}

export function getException(exceptionId: string): Promise<AttendanceException> {
  return request<AttendanceException>({
    method: 'GET',
    path: `/api/v1/attendance/exceptions/${encodeURIComponent(exceptionId)}`,
  })
}

export async function uploadProof(
  exceptionId: string,
  file: File,
): Promise<ProofUploadResponse> {
  // Backend applies `Depends(require_signed_request)` on this route
  // (src/api/routes/attendance.py). The signature must be computed over the
  // multipart body bytes — mirror documentApi.uploadDocument.
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const path = `/api/v1/attendance/exceptions/${encodeURIComponent(exceptionId)}/proof`

  const fileBytes = new Uint8Array(await file.arrayBuffer())

  const headers: Record<string, string> = {}
  if (auth.tokens?.access_token) headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  await addSigningHeaders(headers, 'POST', path, fileBytes)

  const form = new FormData()
  form.append('file', file)

  const r = await fetch(path, {
    method: 'POST',
    body: form,
    credentials: 'same-origin',
    headers,
  })
  const body = await r.json()
  if (!r.ok) throw new Error(body?.error?.message ?? `HTTP ${r.status}`)
  return body.data
}

export function submitReview(
  exceptionId: string,
  data: ReviewDecisionCreate,
): Promise<ExceptionReviewStep> {
  return request<ExceptionReviewStep>({
    method: 'POST',
    path: `/api/v1/attendance/exceptions/${encodeURIComponent(exceptionId)}/review`,
    body: data,
  })
}
