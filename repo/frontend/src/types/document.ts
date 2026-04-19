// Document DTOs — shape mirrors backend `schemas/document.py`. Prior versions
// used fictional fields (`stored_path`, `file_size_bytes`, `versions[]`,
// `reviews[]`, `version_id` on upload responses) that the backend does not
// return. `Document` carries a single `latest_version` instead of arrays;
// historical versions/reviews are fetched via dedicated endpoints.

export type DocumentStatus = 'pending_review' | 'approved' | 'rejected' | 'needs_resubmission'

// BE `DocumentVersionRead`.
export interface DocumentVersion {
  id: string
  document_id: string
  version_number: number
  original_filename: string
  content_type: string
  size_bytes: number
  sha256_hash: string
  uploaded_by: string
  uploaded_at: string
  is_active: boolean
}

// BE `DocumentReviewRead`.
export interface DocumentReview {
  id: string
  document_id: string
  version_id: string
  reviewer_id: string
  status: DocumentStatus
  resubmission_reason: string | null
  reviewer_notes: string | null
  decided_at: string
  created_at: string
}

// BE `DocumentRead`. `requirement_code` is populated server-side from the
// joined DocumentRequirement row (null when the document is unbound), so FE
// does not need a separate requirements lookup per row.
export interface Document {
  id: string
  candidate_id: string
  requirement_id: string | null
  requirement_code: string | null
  document_type: string
  current_version: number
  current_status: DocumentStatus
  resubmission_reason: string | null
  created_at: string
  updated_at: string
  latest_version: DocumentVersion | null
}

// BE `DocumentUploadResponse`. Prior FE shape (`version_id`, `stored_path`)
// was invented — the real endpoint returns the uploaded version metadata
// directly (same fields that appear on DocumentVersionRead minus is_active).
export interface DocumentUploadResponse {
  document_id: string
  version_number: number
  original_filename: string
  content_type: string
  size_bytes: number
  sha256_hash: string
  status: DocumentStatus
  uploaded_at: string
}

export interface DocumentReviewCreate {
  version_id: string
  status: DocumentStatus
  resubmission_reason?: string | null
  reviewer_notes?: string | null
}

// BE `DocumentRequirementRead`. Prior FE used `code`/`label`; the backend
// fields are `requirement_code`/`display_name`.
export interface DocumentRequirement {
  id: string
  requirement_code: string
  display_name: string
  description: string | null
  is_mandatory: boolean
  allowed_mime_types: string[]
  max_size_bytes: number
}

// BE `ChecklistItemRead`. Prior FE used `label`/`description`/
// `document_status`/`submitted_at` which the backend does not return.
export interface ChecklistItemRead {
  requirement_id: string
  requirement_code: string
  display_name: string
  is_mandatory: boolean
  status: DocumentStatus | null
  document_id: string | null
  version_number: number | null
}
