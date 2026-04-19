// Permission checks colocated with the role enum. Views call these rather
// than hand-comparing role strings so a central change here propagates.

import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { Role } from '@/types/auth'

export function usePermissions() {
  const auth = useAuthStore()

  const currentRole = computed<Role | null>(() => auth.role)

  function isRole(target: Role): boolean {
    return auth.role === target
  }

  function canAccess(required: Role | Role[]): boolean {
    if (!auth.role) return false
    const allowed = Array.isArray(required) ? required : [required]
    return allowed.includes(auth.role)
  }

  const isStaff = computed(
    () => auth.role === 'proctor' || auth.role === 'reviewer' || auth.role === 'admin',
  )
  const isAdmin = computed(() => auth.role === 'admin')
  const isCandidate = computed(() => auth.role === 'candidate')

  return { currentRole, isRole, canAccess, isStaff, isAdmin, isCandidate }
}
