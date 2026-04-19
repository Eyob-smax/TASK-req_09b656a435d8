import { addSigningHeaders, request } from './http'
import type { Document, DocumentReviewCreate, DocumentReview, DocumentUploadResponse } from '@/types/document'

// Upload a document for a candidate. Upload is a signed multipart request —
// headers are computed over the raw multipart bytes. Response shape mirrors
// BE `DocumentUploadResponse` (no `version_id`/`stored_path`).
export async function uploadDocument(
  candidateId: string,
  file: File,
  requirementCode?: string | null,
): Promise<DocumentUploadResponse> {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const path = `/api/v1/candidates/${encodeURIComponent(candidateId)}/documents/upload`

  const fileBytes = new Uint8Array(await file.arrayBuffer())

  const headers: Record<string, string> = {}
  if (auth.tokens?.access_token) {
    headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  }
  await addSigningHeaders(headers, 'POST', path, fileBytes)

  const form = new FormData()
  form.append('file', file)
  if (requirementCode) form.append('requirement_code', requirementCode)

  const r = await fetch(path, {
    method: 'POST',
    body: form,
    credentials: 'same-origin',
    headers,
  })
  const body = await r.json()
  if (!r.ok) {
    const err: Error & { status?: number; envelope?: unknown } = new Error(
      body?.error?.message ?? `HTTP ${r.status}`,
    )
    err.status = r.status
    err.envelope = body
    throw err
  }
  return body.data
}

export function listDocuments(candidateId: string): Promise<Document[]> {
  return request<Document[]>({
    method: 'GET',
    path: `/api/v1/candidates/${encodeURIComponent(candidateId)}/documents`,
  })
}

export function getDocument(candidateId: string, documentId: string): Promise<Document> {
  return request<Document>({
    method: 'GET',
    path: `/api/v1/candidates/${encodeURIComponent(candidateId)}/documents/${encodeURIComponent(documentId)}`,
  })
}

export function reviewDocument(
  documentId: string,
  data: DocumentReviewCreate,
): Promise<DocumentReview> {
  return request<DocumentReview>({
    method: 'POST',
    path: `/api/v1/documents/${encodeURIComponent(documentId)}/review`,
    body: data,
  })
}

export function getDownloadUrl(documentId: string): string {
  return `/api/v1/documents/${encodeURIComponent(documentId)}/download`
}

export async function downloadDocument(
  documentId: string,
): Promise<{ blob: Blob; filename: string }> {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  const headers: Record<string, string> = {}
  if (auth.tokens?.access_token) {
    headers['Authorization'] = `Bearer ${auth.tokens.access_token}`
  }
  const r = await fetch(`/api/v1/documents/${encodeURIComponent(documentId)}/download`, {
    method: 'GET',
    credentials: 'same-origin',
    headers,
  })
  if (!r.ok) throw new Error(`Download failed: HTTP ${r.status}`)
  const disposition = r.headers.get('Content-Disposition') ?? ''
  const match = disposition.match(/filename="([^"]+)"/)
  const filename = match ? match[1] : 'document'
  const blob = await r.blob()
  return { blob, filename }
}
