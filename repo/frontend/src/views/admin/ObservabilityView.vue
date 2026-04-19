<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const admin = useAdminStore()
const traceSearch = ref('')
const cacheStatsLoaded = ref(false)

onMounted(async () => {
  await admin.loadMetrics()
  await admin.loadCacheStats()
  cacheStatsLoaded.value = true
})
</script>

<template>
  <div class="observability-view" data-testid="observability-view">
    <h2>Observability</h2>

    <section class="obs-section">
      <h3>Metrics Summary</h3>
      <LoadingSpinner v-if="admin.loading && !admin.metricsSummary" label="Loading metrics…" />
      <EmptyState v-else-if="!admin.metricsSummary" message="No metrics available." />
      <div v-else class="metrics-grid" data-testid="metrics-summary">
        <div
          v-for="(metric, name) in admin.metricsSummary"
          :key="name"
          class="metric-card"
          :data-testid="`metric-card-${name}`"
        >
          <div class="metric-card__name">{{ name }}</div>
          <div class="metric-card__type">{{ (metric as Record<string, unknown>).type }}</div>
          <div class="metric-card__value">
            <template v-if="(metric as Record<string, unknown>).type === 'counter'">
              {{ (metric as Record<string, unknown>).total }}
            </template>
            <template v-else>
              {{ ((metric as Record<string, unknown>).observations as number) }} obs /
              avg {{ ((metric as Record<string, unknown>).avg as number | undefined)?.toFixed(3) }}s
            </template>
          </div>
        </div>
      </div>
    </section>

    <section class="obs-section">
      <h3>Cache Hit Rate</h3>
      <LoadingSpinner v-if="!cacheStatsLoaded" label="Loading cache stats…" />
      <EmptyState
        v-else-if="admin.cacheStats.length === 0"
        message="No cache statistics recorded yet."
      />
      <table v-else class="obs-table" data-testid="cache-stats-table">
        <thead>
          <tr>
            <th>Window Start</th><th>Asset Group</th>
            <th>Total</th><th>Hits</th><th>Misses</th><th>Hit Rate</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="stat in admin.cacheStats" :key="stat.id">
            <td>{{ new Date(stat.window_start).toLocaleString() }}</td>
            <td>{{ stat.asset_group }}</td>
            <td>{{ stat.total_requests }}</td>
            <td>{{ stat.cache_hits }}</td>
            <td>{{ stat.cache_misses }}</td>
            <td>
              {{ stat.hit_rate_pct != null ? stat.hit_rate_pct.toFixed(1) + '%' : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="obs-section">
      <h3>Trace Search</h3>
      <div class="trace-search">
        <input
          v-model="traceSearch"
          placeholder="Enter trace ID"
          class="trace-input"
          data-testid="trace-search-input"
        />
        <p class="trace-hint">
          Trace IDs appear in the <code>X-Request-ID</code> response header and in structured logs.
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.observability-view { display: flex; flex-direction: column; gap: 1.5rem; }
.observability-view h2 { margin: 0; }
.obs-section h3 { margin: 0 0 0.75rem; font-size: 1rem; }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; }
.metric-card { background: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 6px; padding: 0.75rem; }
.metric-card__name { font-size: 0.7rem; color: #555; word-break: break-all; }
.metric-card__type { font-size: 0.65rem; color: #888; margin-bottom: 0.25rem; }
.metric-card__value { font-size: 1.1rem; font-weight: 700; color: #1565c0; }
.obs-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.obs-table th, .obs-table td { padding: 0.4rem 0.6rem; border: 1px solid #e0e0e0; text-align: left; }
.obs-table th { background: #f5f5f5; }
.trace-search { display: flex; flex-direction: column; gap: 0.5rem; }
.trace-input { border: 1px solid #ccc; border-radius: 4px; padding: 0.3rem 0.5rem; font-size: 0.875rem; width: 320px; }
.trace-hint { font-size: 0.8rem; color: #777; margin: 0; }
</style>
