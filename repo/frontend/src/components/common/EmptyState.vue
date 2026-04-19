<script setup lang="ts">
defineProps<{ message?: string; icon?: string }>()
</script>

<template>
  <div class="empty-state" data-testid="empty-state">
    <span class="empty-state__icon" aria-hidden="true">{{ icon ?? '📭' }}</span>
    <p class="empty-state__message">{{ message ?? 'Nothing to show yet.' }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.5rem; padding: 2.5rem 1rem; color: #888;
}
.empty-state__icon { font-size: 2rem; }
.empty-state__message { margin: 0; font-size: 0.9rem; }
</style>
