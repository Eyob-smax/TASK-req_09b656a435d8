<script setup lang="ts">
defineProps<{ label?: string; size?: 'sm' | 'md' | 'lg' }>()
</script>

<template>
  <div class="spinner-wrap" :class="[`spinner-wrap--${size ?? 'md'}`]" role="status" :aria-label="label ?? 'Loading'">
    <div class="spinner" />
    <span v-if="label" class="spinner-label">{{ label }}</span>
  </div>
</template>

<style scoped>
.spinner-wrap { display: flex; align-items: center; gap: 0.5rem; }
.spinner {
  border: 2px solid #e0e0e0;
  border-top-color: #1565c0;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.spinner-wrap--sm .spinner { width: 14px; height: 14px; }
.spinner-wrap--md .spinner { width: 20px; height: 20px; }
.spinner-wrap--lg .spinner { width: 32px; height: 32px; }
.spinner-label { font-size: 0.875rem; color: #555; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
