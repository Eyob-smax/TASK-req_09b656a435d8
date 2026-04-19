// Candidate-scoped DTOs — shape must mirror backend `schemas/candidate.py`
// and `schemas/document.py::ChecklistItemRead` exactly. Prior versions used
// fictional fields (full_name/date_of_birth/national_id/phone/address/etc)
// that the backend does not return. Masked PII lives in *_display fields.

import type { DocumentStatus } from './document'

export interface CandidateProfile {
  id: string
  user_id: string
  preferred_name: string | null
  application_year: number | null
  application_status: string
  program_code: string | null
  created_at: string
  updated_at: string
  // Masked by default (last-4 / year-only). BE lives in `schemas/candidate.py`.
  ssn_display: string | null
  dob_display: string | null
  phone_display: string | null
  email_display: string | null
}

export interface CandidateProfileUpdate {
  preferred_name?: string | null
  application_year?: number | null
  program_code?: string | null
  notes?: string | null
}

export interface ExamScore {
  id: string
  candidate_id: string
  subject_code: string
  subject_name: string
  score: string
  max_score: string | null
  exam_date: string | null
  recorded_by: string | null
  created_at: string
}

export interface ExamScoreCreate {
  subject_code: string
  subject_name: string
  score: string
  max_score?: string | null
  exam_date?: string | null
}

export interface TransferPreference {
  id: string
  candidate_id: string
  institution_name: string
  program_code: string | null
  priority_rank: number
  notes: string | null
  is_active: boolean
  created_at: string
}

export interface TransferPreferenceCreate {
  institution_name: string
  program_code?: string | null
  priority_rank: number
  notes?: string | null
}

export interface TransferPreferenceUpdate {
  institution_name?: string
  program_code?: string | null
  priority_rank?: number
  notes?: string | null
  is_active?: boolean
}

export interface ChecklistItem {
  requirement_id: string
  requirement_code: string
  display_name: string
  is_mandatory: boolean
  status: DocumentStatus | null
  document_id: string | null
  version_number: number | null
}
