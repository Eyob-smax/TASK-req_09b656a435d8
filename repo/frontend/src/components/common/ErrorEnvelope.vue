<script setup lang="ts">
// Renders an API error envelope. All values pass through Vue's text
// interpolation (no v-html), so backend messages cannot inject markup.

import type { AuthError } from '@/types/auth'

defineProps<{ error: AuthError | null }>()
</script>

<template>
  <div v-if="error" class="error-envelope" role="alert">
    <p class="error-envelope__message">{{ error.message }}</p>
    <ul v-if="error.details && error.details.length" class="error-envelope__details">
      <li v-for="(d, idx) in error.details" :key="idx">
        <strong>{{ d.field }}:</strong> {{ d.message }}
      </li>
    </ul>
    <p class="error-envelope__code">code: {{ error.code }}</p>
  </div>
</template>

<style scoped>
.error-envelope {
  border: 1px solid #c62828;
  background: #fff5f5;
  color: #8b0000;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin: 0.5rem 0;
}
.error-envelope__message { font-weight: 600; margin: 0 0 0.25rem; }
.error-envelope__code { font-size: 0.75rem; opacity: 0.7; margin: 0.25rem 0 0; }
.error-envelope__details { margin: 0.25rem 0 0 1rem; padding: 0; }
</style>
