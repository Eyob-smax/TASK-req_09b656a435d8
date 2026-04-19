// FE-UNIT: router guards redirect unauthenticated callers to /login and
// mismatched roles to /forbidden, and preserve the original path via
// `redirect` query so LoginView can return the user after sign-in.

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import { requireAuthGuard, requireRoleGuard } from '@/router/guards'
import { useAuthStore } from '@/stores/auth'
import type { RouteLocationNormalized } from 'vue-router'

function makeRoute(
  path: string,
  meta: Record<string, unknown> = {},
): RouteLocationNormalized {
  return {
    path,
    fullPath: path,
    name: undefined,
    params: {},
    query: {},
    hash: '',
    matched: [],
    meta,
    redirectedFrom: undefined,
  } as unknown as RouteLocationNormalized
}

describe('router guards', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('redirects unauthenticated users to /login preserving redirect', () => {
    const to = makeRoute('/candidate', { requiresAuth: true })
    // @ts-expect-error — guard signature is shaped for the router runtime
    const result = requireAuthGuard(to, makeRoute('/'), () => {})
    expect(result).toMatchObject({
      name: 'login',
      query: { redirect: '/candidate' },
    })
  })

  it('allows authenticated users to pass', () => {
    const auth = useAuthStore()
    auth.setTokens({
      access_token: 'a',
      refresh_token: 'r',
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
    auth.role = 'candidate'
    const to = makeRoute('/candidate', { requiresAuth: true })
    // @ts-expect-error — shaped to match runtime
    const result = requireAuthGuard(to, makeRoute('/'), () => {})
    expect(result).toBe(true)
  })

  it('redirects to /forbidden on role mismatch', () => {
    const auth = useAuthStore()
    auth.role = 'candidate'
    const to = makeRoute('/admin', { requiresAuth: true, role: 'admin' })
    // @ts-expect-error — shaped to match runtime
    const result = requireRoleGuard(to, makeRoute('/'), () => {})
    expect(result).toMatchObject({ name: 'forbidden' })
  })

  it('accepts role when meta declares an array of roles', () => {
    const auth = useAuthStore()
    auth.role = 'proctor'
    const to = makeRoute('/staff', { requiresAuth: true, role: ['proctor', 'reviewer'] })
    // @ts-expect-error — shaped to match runtime
    const result = requireRoleGuard(to, makeRoute('/'), () => {})
    expect(result).toBe(true)
  })

  it('integrates into a real router', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', name: 'login', component: { template: '<div>login</div>' } },
        { path: '/forbidden', name: 'forbidden', component: { template: '<div>forbidden</div>' } },
        {
          path: '/admin',
          name: 'admin',
          meta: { requiresAuth: true, role: 'admin' },
          component: { template: '<div>admin</div>' },
        },
      ],
    })
    router.beforeEach(requireAuthGuard)
    router.beforeEach(requireRoleGuard)
    await router.push('/admin')
    expect(router.currentRoute.value.name).toBe('login')
  })
})
