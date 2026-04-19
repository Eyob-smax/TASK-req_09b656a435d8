<script setup lang="ts">
defineProps<{ count: number; label?: string }>()
</script>

<template>
  <span class="queue-badge" data-testid="queue-badge" :aria-label="`${count} ${label ?? 'items'}`">
    {{ count }}
  </span>
</template>

<style scoped>
.queue-badge {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 1.25rem; height: 1.25rem; padding: 0 0.3rem;
  background: #ef4444; color: white; border-radius: 999px;
  font-size: 0.7rem; font-weight: 700; line-height: 1;
}
</style>
