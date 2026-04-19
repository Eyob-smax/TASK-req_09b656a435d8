<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import { triggerForecast } from '@/services/adminApi'

const admin = useAdminStore()
const triggering = ref(false)
const triggerError = ref<string | null>(null)

onMounted(async () => {
  await admin.loadForecasts()
})

async function runForecast() {
  triggering.value = true
  triggerError.value = null
  try {
    await triggerForecast()
    await admin.loadForecasts()
  } catch (e) {
    triggerError.value = (e as Error).message
  } finally {
    triggering.value = false
  }
}
</script>

<template>
  <div class="forecast-view" data-testid="forecast-view">
    <div class="forecast-header">
      <h2>Capacity &amp; Bandwidth Forecasts</h2>
      <button class="btn-trigger" data-testid="trigger-forecast-btn" :disabled="triggering" @click="runForecast">
        {{ triggering ? 'Computing…' : 'Compute Now' }}
      </button>
    </div>
    <p v-if="triggerError" class="forecast-error">{{ triggerError }}</p>

    <LoadingSpinner v-if="admin.loading && admin.forecasts.length === 0" label="Loading forecasts…" />
    <EmptyState
      v-else-if="admin.forecasts.length === 0"
      message="No forecast snapshots yet. Click 'Compute Now' to generate one."
    />
    <table v-else class="forecast-table" data-testid="forecast-table">
      <thead>
        <tr>
          <th>Computed At</th>
          <th>Horizon (days)</th>
          <th>Input Window (days)</th>
          <th>Bandwidth P50</th>
          <th>Bandwidth P95</th>
          <th>Avg Daily Requests</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="snap in admin.forecasts" :key="snap.id" data-testid="forecast-row">
          <td><TimestampDisplay :value="snap.computed_at" /></td>
          <td>{{ snap.forecast_horizon_days }}</td>
          <td>{{ snap.input_window_days }}</td>
          <td>
            {{ snap.bandwidth_p50_bytes != null ? (snap.bandwidth_p50_bytes / 1_048_576).toFixed(1) + ' MB' : '—' }}
          </td>
          <td>
            {{ snap.bandwidth_p95_bytes != null ? (snap.bandwidth_p95_bytes / 1_048_576).toFixed(1) + ' MB' : '—' }}
          </td>
          <td>
            {{ snap.upload_volume_trend?.avg_daily_requests ?? '—' }}
          </td>
        </tr>
      </tbody>
    </table>
    <p class="forecast-total" v-if="admin.forecastTotal > 0">
      {{ admin.forecastTotal }} total snapshots
    </p>
  </div>
</template>

<style scoped>
.forecast-view { display: flex; flex-direction: column; gap: 1.25rem; }
.forecast-header { display: flex; justify-content: space-between; align-items: center; }
.forecast-header h2 { margin: 0; }
.btn-trigger { padding: 0.4rem 1rem; background: #1565c0; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-trigger:disabled { opacity: 0.6; cursor: not-allowed; }
.forecast-error { color: #c62828; font-size: 0.85rem; margin: 0; }
.forecast-total { font-size: 0.8rem; color: #666; margin: 0; }
.forecast-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.forecast-table th, .forecast-table td { padding: 0.4rem 0.6rem; border: 1px solid #e0e0e0; text-align: left; }
.forecast-table th { background: #f5f5f5; font-weight: 600; }
</style>
