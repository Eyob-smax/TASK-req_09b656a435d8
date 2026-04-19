import { APIRequestContext, Page, request as pwRequest } from '@playwright/test'

// Live PW_LIVE_* credential bundle. Each credential pair is optional — specs
// that need a role call `requireLive(...)` up-front and skip if their slice is
// missing. This mirrors the discipline in `unit_tests/browser/live_auth_smoke.spec.ts`.
export interface LiveCreds {
  candidateUsername?: string
  candidatePassword?: string
  reviewerUsername?: string
  reviewerPassword?: string
  adminUsername?: string
  adminPassword?: string
}

export function readLiveCreds(): LiveCreds {
  return {
    candidateUsername: process.env.PW_LIVE_USERNAME,
    candidatePassword: process.env.PW_LIVE_PASSWORD,
    reviewerUsername: process.env.PW_LIVE_REVIEWER_USERNAME,
    reviewerPassword: process.env.PW_LIVE_REVIEWER_PASSWORD,
    adminUsername: process.env.PW_LIVE_ADMIN_USERNAME,
    adminPassword: process.env.PW_LIVE_ADMIN_PASSWORD,
  }
}

// Role-aware env gate. Returns a skip reason when any required var is missing;
// specs call `test.skip(...)` with the returned reason.
export function missingLiveVars(roles: Array<'candidate' | 'reviewer' | 'admin'>): string | null {
  const creds = readLiveCreds()
  const missing: string[] = []
  for (const role of roles) {
    if (role === 'candidate' && (!creds.candidateUsername || !creds.candidatePassword)) {
      missing.push('PW_LIVE_USERNAME, PW_LIVE_PASSWORD')
    }
    if (role === 'reviewer' && (!creds.reviewerUsername || !creds.reviewerPassword)) {
      missing.push('PW_LIVE_REVIEWER_USERNAME, PW_LIVE_REVIEWER_PASSWORD')
    }
    if (role === 'admin' && (!creds.adminUsername || !creds.adminPassword)) {
      missing.push('PW_LIVE_ADMIN_USERNAME, PW_LIVE_ADMIN_PASSWORD')
    }
  }
  return missing.length > 0 ? `Missing live env vars: ${missing.join('; ')}` : null
}

function isoNow(): string {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z')
}

function nonce(): string {
  return `n-${Math.random().toString(16).slice(2, 10)}${Math.random().toString(16).slice(2, 10)}`
}

// Browser-side Web Crypto signing wrapper. Runs in-page via page.evaluate so
// the key material never leaves the live origin — same code path production
// uses through `services/deviceKey.ts`.
export interface DeviceHandle {
  deviceId: string
  // Inside the page, the priv key lives on window.__liveDevicePriv for later
  // signed requests. Outside the page we only hold the device_id.
}

async function loginRequest(apiReq: APIRequestContext, username: string, password: string) {
  const resp = await apiReq.post('/api/v1/auth/login', {
    data: {
      username,
      password,
      nonce: nonce(),
      timestamp: isoNow(),
    },
  })
  if (!resp.ok()) {
    throw new Error(`Login failed (${resp.status()}): ${await resp.text()}`)
  }
  const body = await resp.json()
  return body.data.access_token as string
}

// Login-by-UI: drives the real /login page against the live backend without
// stubs. Leaves session storage populated so subsequent `page.request` calls
// inherit whatever session cookies / bearer-token handoff the app uses.
export async function loginAs(
  page: Page,
  role: 'candidate' | 'reviewer' | 'admin',
): Promise<string> {
  const creds = readLiveCreds()
  let username: string | undefined
  let password: string | undefined
  if (role === 'candidate') {
    username = creds.candidateUsername
    password = creds.candidatePassword
  } else if (role === 'reviewer') {
    username = creds.reviewerUsername
    password = creds.reviewerPassword
  } else {
    username = creds.adminUsername
    password = creds.adminPassword
  }
  if (!username || !password) {
    throw new Error(`Missing PW_LIVE_* credentials for role=${role}`)
  }
  await page.goto('/login')
  await page.getByTestId('login-username').fill(username)
  await page.getByTestId('login-password').fill(password)
  await page.getByTestId('login-submit').click()
  await page.waitForURL(/\/(candidate|staff|admin)(\/|$)/, { timeout: 15000 })
  return await loginRequest(page.request, username, password)
}

// Enroll a fresh device via the real /auth/device/challenge + /activate flow.
// Runs entirely in-page with window.crypto.subtle — same path as production
// `services/deviceKey.ts`. Returns the server-assigned device_id.
export async function registerLiveDevice(page: Page, token: string): Promise<DeviceHandle> {
  const deviceId: string = await page.evaluate(async (bearer: string) => {
    const subtle = window.crypto.subtle
    const pair = await subtle.generateKey(
      { name: 'ECDSA', namedCurve: 'P-256' },
      true,
      ['sign', 'verify'],
    )
    const spki = await subtle.exportKey('spki', pair.publicKey)
    const b64 = btoa(String.fromCharCode(...new Uint8Array(spki)))
    const pem = [
      '-----BEGIN PUBLIC KEY-----',
      ...(b64.match(/.{1,64}/g) ?? []),
      '-----END PUBLIC KEY-----',
      '',
    ].join('\n')
    const fingerprint = 'fp-' + Math.random().toString(16).slice(2, 18)
    const headers = { Authorization: `Bearer ${bearer}`, 'Content-Type': 'application/json' }

    const challengeResp = await fetch('/api/v1/auth/device/challenge', {
      method: 'POST',
      headers,
      body: JSON.stringify({ device_fingerprint: fingerprint, public_key_pem: pem }),
    })
    const challenge = (await challengeResp.json()).data
    const nonceBytes = new TextEncoder().encode(challenge.nonce)
    const signature = await subtle.sign(
      { name: 'ECDSA', hash: 'SHA-256' },
      pair.privateKey,
      nonceBytes,
    )
    const sigB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))

    const activateResp = await fetch('/api/v1/auth/device/activate', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        challenge_id: challenge.challenge_id,
        device_fingerprint: fingerprint,
        public_key_pem: pem,
        signature: sigB64,
        label: 'e2e-live',
      }),
    })
    const activated = (await activateResp.json()).data
    // Stash the private key for later signed calls initiated from the page.
    ;(window as unknown as { __liveDevicePriv: CryptoKey }).__liveDevicePriv = pair.privateKey
    ;(window as unknown as { __liveDeviceId: string }).__liveDeviceId = activated.device_id
    return activated.device_id
  }, token)
  return { deviceId }
}

// Fresh API request context scoped to the Vite proxy. Used by serverSeed for
// admin-authored fixture setup (DB seeding calls the real backend via HTTPS
// through the proxy — no mocks).
export async function newApiContext(): Promise<APIRequestContext> {
  return await pwRequest.newContext({ baseURL: 'http://localhost:5173' })
}
