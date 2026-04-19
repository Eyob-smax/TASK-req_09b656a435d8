// Router guards: enforce authentication on `requiresAuth` routes and role
// match on routes that declare `meta.role`. Both redirect to explicit pages
// (`/login`, `/forbidden`) rather than throwing so the router surfaces the
// condition to the user.

import type { NavigationGuardWithThis, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { Role } from '@/types/auth'

function metaRoles(to: RouteLocationNormalized): Role[] | null {
  const raw = to.meta?.role
  if (!raw) return null
  return Array.isArray(raw) ? (raw as Role[]) : [raw as Role]
}

export const requireAuthGuard: NavigationGuardWithThis<undefined> = (to) => {
  if (!to.meta?.requiresAuth) return true
  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }
  return true
}

export const requireRoleGuard: NavigationGuardWithThis<undefined> = (to) => {
  const allowed = metaRoles(to)
  if (!allowed) return true
  const auth = useAuthStore()
  if (!auth.role || !allowed.includes(auth.role)) {
    return { name: 'forbidden' }
  }
  return true
}
