<script setup lang="ts">
import TimestampDisplay from './TimestampDisplay.vue'

export interface TimelineEntry {
  id: string
  label: string
  description?: string | null
  timestamp: string
  actor?: string | null
}

defineProps<{ entries: TimelineEntry[] }>()
</script>

<template>
  <ol class="timeline" data-testid="timeline-list">
    <li v-if="entries.length === 0" class="timeline__empty">No events yet.</li>
    <li v-for="entry in entries" :key="entry.id" class="timeline__item">
      <span class="timeline__dot" aria-hidden="true" />
      <div class="timeline__content">
        <strong class="timeline__label">{{ entry.label }}</strong>
        <p v-if="entry.description" class="timeline__desc">{{ entry.description }}</p>
        <div class="timeline__meta">
          <TimestampDisplay :value="entry.timestamp" />
          <span v-if="entry.actor" class="timeline__actor">· {{ entry.actor }}</span>
        </div>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.timeline { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0; }
.timeline__empty { color: #888; font-size: 0.875rem; padding: 0.5rem 0; }
.timeline__item {
  display: flex; gap: 0.75rem; position: relative;
  padding-bottom: 1rem;
}
.timeline__item:not(:last-child)::before {
  content: ''; position: absolute; left: 5px; top: 14px;
  bottom: 0; width: 2px; background: #e0e0e0;
}
.timeline__dot {
  width: 12px; height: 12px; border-radius: 50%; background: #1565c0;
  flex-shrink: 0; margin-top: 3px;
}
.timeline__content { flex: 1; min-width: 0; }
.timeline__label { font-size: 0.875rem; }
.timeline__desc { font-size: 0.8rem; color: #555; margin: 0.125rem 0 0; }
.timeline__meta { font-size: 0.75rem; color: #888; margin-top: 0.125rem; display: flex; gap: 0.25rem; }
.timeline__actor { color: #888; }
</style>
