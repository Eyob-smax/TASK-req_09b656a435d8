// FE-UNIT: attendanceApi.uploadProof must attach request-signing headers (H4).
// The backend route POST /api/v1/attendance/exceptions/{id}/proof sits behind
// `Depends(require_signed_request)` (src/api/routes/attendance.py), so the
// prior naked-fetch upload would have 400'd with SIGNATURE_INVALID.

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock deviceKey to avoid IndexedDB dependency in JSDOM.
vi.mock('@/services/deviceKey', () => ({
  getOrCreateDeviceKey: vi.fn(async () => ({
    id: 'current',
    privateKey: {} as CryptoKey,
    publicKey: {} as CryptoKey,
    deviceId: 'dev-uuid-123',
    fingerprint: 'fp-abc',
    publicKeyPem: '-----BEGIN PUBLIC KEY-----\nx\n-----END PUBLIC KEY-----\n',
    createdAt: '2024-01-01T00:00:00Z',
  })),
  setDeviceId: vi.fn(),
  clearDeviceKey: vi.fn(),
}))

vi.mock('@/services/requestSigner', async (orig) => {
  const actual = await orig<typeof import('@/services/requestSigner')>()
  return {
    ...actual,
    signRequest: vi.fn(async () => 'fake-base64-signature=='),
    currentTimestamp: () => '2026-04-19T00:00:00Z',
    generateNonce: () => 'n-deadbeef',
  }
})

import { uploadProof } from '@/services/attendanceApi'
import { useAuthStore } from '@/stores/auth'

describe('attendanceApi.uploadProof', () => {
  let originalFetch: typeof fetch

  beforeEach(() => {
    setActivePinia(createPinia())
    originalFetch = globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('attaches ECDSA signing headers (X-Request-Signature, X-Nonce, X-Timestamp, X-Device-ID)', async () => {
    const auth = useAuthStore()
    auth.$patch({
      tokens: {
        access_token: 'tok',
        refresh_token: 'ref',
        token_type: 'bearer',
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      },
    } as Parameters<typeof auth.$patch>[0])

    const capturedHeaders: Record<string, string> = {}
    globalThis.fetch = vi.fn(async (_url: RequestInfo | URL, init?: RequestInit) => {
      const h = init?.headers as Record<string, string> | undefined
      if (h) Object.assign(capturedHeaders, h)
      return new Response(
        JSON.stringify({
          data: {
            version_number: 1,
            original_filename: 'x.pdf',
            content_type: 'application/pdf',
            size_bytes: 4,
            sha256_hash: 'h',
            status: 'pending',
            uploaded_at: '2024-01-01T00:00:00Z',
          },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      )
    }) as unknown as typeof fetch

    const file = new File([new Uint8Array([1, 2, 3, 4])], 'proof.pdf', {
      type: 'application/pdf',
    })
    await uploadProof('exc-1', file)

    expect(capturedHeaders['X-Request-Signature']).toBe('fake-base64-signature==')
    expect(capturedHeaders['X-Nonce']).toBe('n-deadbeef')
    expect(capturedHeaders['X-Timestamp']).toBe('2026-04-19T00:00:00Z')
    expect(capturedHeaders['X-Device-ID']).toBe('dev-uuid-123')
    expect(capturedHeaders['Authorization']).toBe('Bearer tok')
  })
})
