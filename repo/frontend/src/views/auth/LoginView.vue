<script setup lang="ts">
// Login screen. Wires LoginForm → auth store, surfaces envelope errors via
// ErrorEnvelope, and honors the `redirect` query so guard-triggered
// redirects return the user to the original target after login.

import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoginForm from '@/components/auth/LoginForm.vue'
import ErrorEnvelope from '@/components/common/ErrorEnvelope.vue'
import { useAuthStore } from '@/stores/auth'
import { HttpError } from '@/services/http'
import type { AuthError, Role } from '@/types/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const busy = ref(false)
const error = ref<AuthError | null>(null)

const redirectTarget = computed(() => {
  const q = route.query.redirect
  return typeof q === 'string' && q.startsWith('/') ? q : null
})

function roleHome(role: Role | null): string {
  if (role === 'candidate') return '/candidate'
  if (role === 'admin') return '/admin'
  if (role === 'proctor' || role === 'reviewer') return '/staff'
  return '/'
}

async function handleSubmit(payload: { username: string; password: string }): Promise<void> {
  busy.value = true
  error.value = null
  try {
    await auth.login(payload)
    const target = redirectTarget.value ?? roleHome(auth.role)
    await router.replace(target)
  } catch (err) {
    if (err instanceof HttpError) {
      error.value = err.envelope?.error ?? {
        code: 'AUTH_REQUIRED',
        message: 'Login failed.',
      }
    } else {
      error.value = { code: 'NETWORK_ERROR', message: (err as Error).message }
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="login-view">
    <h1 class="login-view__title">MeritTrack — Sign in</h1>
    <ErrorEnvelope :error="error" />
    <LoginForm :busy="busy" :error="error" @submit="handleSubmit" />
  </main>
</template>

<style scoped>
.login-view {
  max-width: 400px; margin: 4rem auto; padding: 1.5rem;
  border: 1px solid #e0e0e0; border-radius: 8px;
}
.login-view__title { margin: 0 0 1rem; font-size: 1.25rem; }
</style>
