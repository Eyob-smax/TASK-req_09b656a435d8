// FE-UNIT: when the server returns SIGNATURE_INVALID the http wrapper must
// surface the envelope to the caller without triggering a refresh loop.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { request, HttpError } from '@/services/http'

function envelope(code: string, message: string) {
  return {
    success: false,
    error: { code, message },
    meta: { trace_id: 't', timestamp: new Date().toISOString() },
  }
}

describe('signature failure handling', () => {
  const originalFetch = globalThis.fetch
  beforeEach(() => setActivePinia(createPinia()))
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('surfaces SIGNATURE_INVALID to caller without retry', async () => {
    const auth = useAuthStore()
    auth.setTokens({
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
      expires_in: 900,
    })
    const refreshSpy = vi.spyOn(auth, 'refresh')

    const calls: string[] = []
    globalThis.fetch = vi.fn(async () => {
      calls.push('fetch')
      return new Response(JSON.stringify(envelope('SIGNATURE_INVALID', 'bad sig')), {
        status: 400,
        headers: { 'content-type': 'application/json' },
      })
    }) as unknown as typeof fetch

    try {
      await request({
        method: 'POST',
        path: '/api/v1/auth/password/change',
        body: { current_password: 'x', new_password: 'y' },
        signed: false, // already attaches via skipAuth=false but we don't want crypto in this test
        skipAuth: true,
      })
      throw new Error('expected throw')
    } catch (err) {
      expect(err).toBeInstanceOf(HttpError)
      const httpErr = err as HttpError
      expect(httpErr.status).toBe(400)
      expect(httpErr.envelope.error.code).toBe('SIGNATURE_INVALID')
    }
    expect(refreshSpy).not.toHaveBeenCalled()
    expect(calls).toHaveLength(1)
  })

  it('does not retry on NONCE_REPLAY', async () => {
    const auth = useAuthStore()
    auth.setTokens({
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
      expires_in: 900,
    })
    const refreshSpy = vi.spyOn(auth, 'refresh')
    globalThis.fetch = vi.fn(async () => {
      return new Response(JSON.stringify(envelope('NONCE_REPLAY', 'nonce')), {
        status: 409,
        headers: { 'content-type': 'application/json' },
      })
    }) as unknown as typeof fetch

    await expect(
      request({ method: 'POST', path: '/api/v1/orders', skipAuth: true, signed: false }),
    ).rejects.toBeInstanceOf(HttpError)
    expect(refreshSpy).not.toHaveBeenCalled()
  })
})
