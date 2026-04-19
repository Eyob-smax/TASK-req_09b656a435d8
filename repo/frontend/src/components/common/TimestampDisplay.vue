<script setup lang="ts">
import { format12h, formatDate } from '@/composables/useTimestamp'

defineProps<{
  value: string | null | undefined
  dateOnly?: boolean
}>()
</script>

<template>
  <time
    :datetime="value ?? ''"
    class="timestamp"
    :title="value ?? ''"
    data-testid="timestamp"
  >
    {{ dateOnly ? formatDate(value) : format12h(value) }}
  </time>
</template>

<style scoped>
.timestamp { font-variant-numeric: tabular-nums; white-space: nowrap; }
</style>
