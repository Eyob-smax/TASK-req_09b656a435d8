<script setup lang="ts">
// Username/password form. Client-side checks mirror the backend policy
// (min 12-char password, non-empty username) so obvious mistakes surface
// without a round-trip; the server remains the source of truth.

import { reactive, ref } from 'vue'
import type { AuthError } from '@/types/auth'

const emit = defineEmits<{
  (e: 'submit', payload: { username: string; password: string }): void
}>()

defineProps<{
  busy?: boolean
  error?: AuthError | null
}>()

const form = reactive({ username: '', password: '' })
const localError = ref<string | null>(null)

function onSubmit(): void {
  localError.value = null
  if (!form.username.trim()) {
    localError.value = 'Username is required.'
    return
  }
  if (form.password.length < 12) {
    localError.value = 'Password must be at least 12 characters.'
    return
  }
  emit('submit', { username: form.username.trim(), password: form.password })
}
</script>

<template>
  <form class="login-form" @submit.prevent="onSubmit">
    <label class="login-form__field">
      <span>Username</span>
      <input
        v-model="form.username"
        type="text"
        autocomplete="username"
        data-testid="login-username"
        required
      />
    </label>
    <label class="login-form__field">
      <span>Password</span>
      <input
        v-model="form.password"
        type="password"
        autocomplete="current-password"
        data-testid="login-password"
        required
      />
    </label>
    <p v-if="localError" class="login-form__local-error" role="alert">
      {{ localError }}
    </p>
    <button
      type="submit"
      class="login-form__submit"
      :disabled="busy"
      data-testid="login-submit"
    >
      {{ busy ? 'Signing in…' : 'Sign in' }}
    </button>
  </form>
</template>

<style scoped>
.login-form { display: flex; flex-direction: column; gap: 0.75rem; }
.login-form__field { display: flex; flex-direction: column; gap: 0.25rem; }
.login-form__field input {
  padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;
}
.login-form__submit {
  padding: 0.5rem 1rem; background: #1565c0; color: white;
  border: none; border-radius: 4px; cursor: pointer;
}
.login-form__submit:disabled { opacity: 0.6; cursor: wait; }
.login-form__local-error { color: #8b0000; margin: 0; font-size: 0.875rem; }
</style>
