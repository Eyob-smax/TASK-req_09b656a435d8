import { APIRequestContext } from '@playwright/test'
import { newApiContext, readLiveCreds } from './liveSeed'

// Lightweight admin-authored fixture helpers. They issue real HTTPS requests
// through the Vite proxy to the live backend — no page.route() stubs, no
// mocked responses. Each helper is idempotent-enough to run per spec.

async function adminLogin(api: APIRequestContext): Promise<string> {
  const creds = readLiveCreds()
  if (!creds.adminUsername || !creds.adminPassword) {
    throw new Error('admin creds (PW_LIVE_ADMIN_*) required for serverSeed')
  }
  const resp = await api.post('/api/v1/auth/login', {
    data: {
      username: creds.adminUsername,
      password: creds.adminPassword,
      nonce: `n-${Math.random().toString(16).slice(2, 18)}`,
      timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
    },
  })
  if (!resp.ok()) throw new Error(`admin login failed: ${resp.status()} ${await resp.text()}`)
  return (await resp.json()).data.access_token as string
}

async function reviewerLogin(api: APIRequestContext): Promise<string> {
  const creds = readLiveCreds()
  if (!creds.reviewerUsername || !creds.reviewerPassword) {
    throw new Error('reviewer creds (PW_LIVE_REVIEWER_*) required for serverSeed')
  }
  const resp = await api.post('/api/v1/auth/login', {
    data: {
      username: creds.reviewerUsername,
      password: creds.reviewerPassword,
      nonce: `n-${Math.random().toString(16).slice(2, 18)}`,
      timestamp: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
    },
  })
  if (!resp.ok()) throw new Error(`reviewer login failed: ${resp.status()}`)
  return (await resp.json()).data.access_token as string
}

export interface SeededOrder {
  orderId: string
  itemId: string
  candidateProfileId?: string
}

// Ensure at least one active ServiceItem exists (reviewer creates via catalog
// admin endpoint if present; otherwise assumes a seed script populated the DB).
// Returns the first listed active item.
export async function ensureServiceItem(api: APIRequestContext, token: string): Promise<string> {
  const resp = await api.get('/api/v1/services', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok()) throw new Error(`GET /services failed: ${resp.status()}`)
  const data = (await resp.json()).data as Array<{ id: string; is_active?: boolean }>
  const first = data.find(item => item.is_active !== false) ?? data[0]
  if (!first) throw new Error('no ServiceItem available — seed the live DB before running live e2e')
  return first.id
}

export async function newServerSeed() {
  const api = await newApiContext()
  const adminToken = await adminLogin(api)
  return {
    api,
    adminToken,
    reviewerToken: async () => reviewerLogin(api),
    ensureServiceItem: () => ensureServiceItem(api, adminToken),
    dispose: async () => api.dispose(),
  }
}
