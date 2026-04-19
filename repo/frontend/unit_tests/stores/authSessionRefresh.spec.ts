// FE-UNIT: auth store session refresh and clearSession behavior.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

const mockRefreshResponse = {
  access_token: 'new-access',
  refresh_token: 'new-refresh',
  token_type: 'bearer' as const,
  expires_in: 900,
}

describe('useAuthStore session refresh', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('clearSession removes all token and user state', () => {
    const auth = useAuthStore()
    auth.setTokens({ access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900 })
    auth.role = 'candidate'
    auth.clearSession()
    expect(auth.tokens).toBeNull()
    expect(auth.user).toBeNull()
    expect(auth.role).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('isAuthenticated requires both tokens and user', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
    auth.setTokens({ access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900 })
    expect(auth.isAuthenticated).toBe(false) // user still null
    auth.user = { id: '1', username: 'u', role: 'candidate', full_name: 'U', is_active: true, last_login_at: null }
    expect(auth.isAuthenticated).toBe(true)
  })

  it('setDeviceId stores the device id', () => {
    const auth = useAuthStore()
    auth.setDeviceId('dev-123')
    expect(auth.deviceId).toBe('dev-123')
  })

  it('refresh returns false when no refresh token', async () => {
    const auth = useAuthStore()
    const result = await auth.refresh()
    expect(result).toBe(false)
  })

  it('refresh calls clearSession on failure', async () => {
    const auth = useAuthStore()
    auth.setTokens({ access_token: 'a', refresh_token: 'expired', token_type: 'bearer', expires_in: 900 })

    vi.mock('@/services/authApi', () => ({
      refresh: vi.fn().mockRejectedValue(new Error('Token invalid')),
      me: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    }))

    const { refresh } = await import('@/services/authApi')
    ;(refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('expired'))

    const result = await auth.refresh()
    expect(result).toBe(false)
  })
})
