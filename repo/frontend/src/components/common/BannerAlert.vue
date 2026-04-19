<script setup lang="ts">
const props = defineProps<{
  type?: 'info' | 'warning' | 'error' | 'success'
  message: string
  dismissible?: boolean
}>()

const emit = defineEmits<{ (e: 'dismiss'): void }>()

const COLOR_MAP = {
  info:    { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  warning: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
  error:   { bg: '#fee2e2', border: '#ef4444', text: '#991b1b' },
  success: { bg: '#dcfce7', border: '#10b981', text: '#065f46' },
}

function colors() {
  return COLOR_MAP[props.type ?? 'info']
}
</script>

<template>
  <div
    class="banner"
    :style="{ background: colors().bg, borderColor: colors().border, color: colors().text }"
    role="alert"
    :data-testid="`banner-${type ?? 'info'}`"
  >
    <span class="banner__message">{{ message }}</span>
    <button v-if="dismissible" class="banner__dismiss" type="button" aria-label="Dismiss" @click="emit('dismiss')">
      &times;
    </button>
  </div>
</template>

<style scoped>
.banner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.625rem 1rem; border: 1px solid; border-radius: 6px;
  font-size: 0.875rem; gap: 0.5rem;
}
.banner__message { flex: 1; }
.banner__dismiss {
  background: none; border: none; cursor: pointer; font-size: 1.1rem;
  line-height: 1; color: inherit; padding: 0;
}
</style>
