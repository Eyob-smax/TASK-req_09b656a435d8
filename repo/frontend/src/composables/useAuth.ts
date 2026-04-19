// Thin wrapper over the auth store so views import a composable rather than
// reaching into the store directly. Keeps component APIs stable if the store
// internals change later.

import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const store = useAuthStore()
  const { user, role, tokens, isAuthenticated, lastError, deviceId } = storeToRefs(store)
  return {
    user,
    role,
    tokens,
    deviceId,
    isAuthenticated,
    lastError,
    login: store.login,
    logout: store.logout,
    refresh: store.refresh,
    loadSession: store.loadSession,
    clearSession: store.clearSession,
  }
}
