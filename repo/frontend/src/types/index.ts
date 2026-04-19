// Core domain type definitions for MeritTrack.
// Extended by each feature module's own types file.

export type UserRole = 'CAND' | 'PRCT' | 'REVW' | 'ADMN'

export interface ApiMeta {
  trace_id: string
  timestamp: string
}

export interface ApiSuccess<T> {
  success: true
  data: T
  meta: ApiMeta
}

export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: Array<{ field: string; message: string }>
  }
  meta: ApiMeta
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError

export interface Pagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiListSuccess<T> {
  success: true
  data: T[]
  pagination: Pagination
  meta: ApiMeta
}

export type OrderStatus =
  | 'pending_payment'
  | 'pending_fulfillment'
  | 'pending_receipt'
  | 'completed'
  | 'canceled'
  | 'refund_in_progress'
  | 'refunded'

export type DocumentStatus =
  | 'pending_review'
  | 'approved'
  | 'rejected'
  | 'needs_resubmission'

export type ExceptionStatus =
  | 'pending_proof'
  | 'pending_initial_review'
  | 'pending_final_review'
  | 'approved'
  | 'rejected'
