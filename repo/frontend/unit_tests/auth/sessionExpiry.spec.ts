// FE-UNIT: on TOKEN_EXPIRED 401, http wrapper calls auth.refresh() once and
// retries; when refresh fails, the session is cleared and no further retries
// are attempted (isRetry flag guards the loop).

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

describe('session expiry flow', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it('refreshes and retries once on TOKEN_EXPIRED', async () => {
    const auth = useAuthStore()
    auth.setTokens({
      access_token: 'a1',
      refresh_token: 'r1',
      token_type: 'bearer',
      expires_in: 900,
    })
    const refreshSpy = vi.spyOn(auth, 'refresh').mockResolvedValue(true)

    const calls: string[] = []
    globalThis.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : (input as Request).url ?? String(input)
      calls.push(url)
      if (calls.length === 1) {
        return new Response(JSON.stringify(envelope('TOKEN_EXPIRED', 'expired')), {
          status: 401,
          headers: { 'content-type': 'application/json' },
        })
      }
      return new Response(
        JSON.stringify({
          success: true,
          data: { ok: true },
          meta: { trace_id: 't', timestamp: new Date().toISOString() },
        }),
        { status: 200, headers: { 'content-type': 'application/json' } },
      )
    }) as unknown as typeof fetch

    const result = await request<{ ok: boolean }>({ method: 'GET', path: '/api/v1/auth/me' })
    expect(result).toEqual({ ok: true })
    expect(refreshSpy).toHaveBeenCalledTimes(1)
    expect(calls).toHaveLength(2)
  })

  it('clears session when refresh fails', async () => {
    const auth = useAuthStore()
    auth.setTokens({
      access_token: 'a1',
      refresh_token: 'r1',
      token_type: 'bearer',
      expires_in: 900,
    })
    auth.user = {
      id: '1',
      username: 'u',
      role: 'candidate',
      full_name: 'U',
      is_active: true,
      last_login_at: null,
    } as never
    vi.spyOn(auth, 'refresh').mockImplementation(async () => {
      auth.clearSession()
      return false
    })

    globalThis.fetch = vi.fn(async () => {
      return new Response(JSON.stringify(envelope('TOKEN_EXPIRED', 'expired')), {
        status: 401,
        headers: { 'content-type': 'application/json' },
      })
    }) as unknown as typeof fetch

    await expect(
      request({ method: 'GET', path: '/api/v1/auth/me' }),
    ).rejects.toBeInstanceOf(HttpError)
    expect(auth.isAuthenticated).toBe(false)
  })
})
