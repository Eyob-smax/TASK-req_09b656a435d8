// Auth-specific TypeScript types. Role codes match the backend UserRole enum
// (single source of truth). The short codes in the router have been migrated
// to the backend string values.

export type Role = 'candidate' | 'proctor' | 'reviewer' | 'admin'

export interface User {
  id: string
  username: string
  role: Role
  full_name: string
  is_active: boolean
  last_login_at: string | null
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface LoginResponse extends TokenPair {
  user_id: string
  role: Role
  cohort_config?: Record<string, unknown> | null
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface MeResponse {
  user: User
  cohort_config?: Record<string, unknown> | null
  device_id?: string | null
  // Resolved candidate profile UUID for role='candidate'; null otherwise.
  // Distinct from `user.id` — CandidateProfile has its own PK with a user_id FK.
  candidate_id?: string | null
}

export interface DeviceRegistration {
  device_id: string
  device_fingerprint: string
  registered_at: string
}

export interface DeviceChallenge {
  challenge_id: string
  nonce: string
  expires_at: string
}

export interface AuthError {
  code: string
  message: string
  details?: Array<{ field: string; message: string }>
}

export interface SignedRequestHeaders {
  'X-Timestamp': string
  'X-Nonce': string
  'X-Device-ID': string
  'X-Request-Signature': string
}
