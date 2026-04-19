<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import { resolveAfterSales } from '@/services/refundApi'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import StatusChip from '@/components/common/StatusChip.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const queue = useQueueStore()
const resolvingId = ref<string | null>(null)
const resolutionNotes = ref('')
const notification = ref<string | null>(null)
const error = ref<string | null>(null)

onMounted(async () => {
  await queue.loadAfterSales()
})

async function resolve(orderId: string, requestId: string): Promise<void> {
  if (!resolutionNotes.value.trim()) return
  try {
    await resolveAfterSales(orderId, requestId, resolutionNotes.value)
    resolvingId.value = null
    resolutionNotes.value = ''
    notification.value = 'After-sales request resolved.'
    await queue.loadAfterSales()
  } catch (e) {
    error.value = (e as Error).message
  }
}
</script>

<template>
  <div class="after-sales-view" data-testid="after-sales-queue-view">
    <h2>After-Sales Queue</h2>

    <BannerAlert v-if="notification" type="success" :message="notification" :dismissible="true" @dismiss="notification = null" />
    <BannerAlert v-if="error" type="error" :message="error" :dismissible="true" @dismiss="error = null" />

    <div v-for="item in queue.afterSales" :key="item.request_id" class="as-card">
      <div class="as-card__head">
        <span class="as-card__type">{{ item.request_type }}</span>
        <StatusChip :status="item.status" size="sm" />
        <span class="as-card__window">Window expires: <TimestampDisplay :value="item.window_expires_at" /></span>
      </div>

      <div v-if="resolvingId === item.request_id" class="as-card__resolve">
        <textarea v-model="resolutionNotes" rows="2" placeholder="Resolution notes (required)" />
        <div class="as-card__resolve-actions">
          <button type="button" class="btn-primary" :disabled="!resolutionNotes.trim()" @click="resolve(item.order_id, item.request_id)">
            Resolve
          </button>
          <button type="button" class="btn-secondary" @click="resolvingId = null">Cancel</button>
        </div>
      </div>
      <button v-else type="button" class="btn-secondary btn-sm" @click="resolvingId = item.request_id">
        Resolve
      </button>
    </div>

    <p v-if="!queue.loading && queue.afterSales.length === 0" class="empty-msg">No after-sales requests pending.</p>
    <PaginationControls :pagination="queue.pagination" @page="queue.loadAfterSales({ page: $event })" />
  </div>
</template>

<style scoped>
.after-sales-view { display: flex; flex-direction: column; gap: 1.25rem; }
.after-sales-view h2 { margin: 0; }
.as-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.as-card__head { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.as-card__type { font-weight: 600; font-size: 0.9rem; }
.as-card__window { font-size: 0.8rem; color: #777; }
.as-card__resolve { display: flex; flex-direction: column; gap: 0.5rem; }
.as-card__resolve textarea { padding: 0.4rem 0.5rem; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 0.875rem; }
.as-card__resolve-actions { display: flex; gap: 0.5rem; }
.btn-primary { padding: 0.5rem 1rem; background: #1565c0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-primary:disabled { opacity: 0.6; }
.btn-secondary { padding: 0.4rem 0.75rem; background: white; color: #1565c0; border: 1px solid #1565c0; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-sm { font-size: 0.8rem; padding: 0.25rem 0.6rem; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
