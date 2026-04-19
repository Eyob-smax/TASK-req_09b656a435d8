<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const queue = useQueueStore()

onMounted(async () => {
  await queue.loadExceptions()
})
</script>

<template>
  <div class="exception-queue-view" data-testid="exception-queue-view">
    <h2>Exception Review Queue</h2>

    <table v-if="queue.exceptions.length > 0" class="queue-table">
      <thead>
        <tr><th>Stage</th><th>Status</th><th>Anomaly Type</th><th>Submitted</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in queue.exceptions" :key="item.exception_id">
          <td>{{ item.current_stage }}</td>
          <td><StatusChip :status="item.status" size="sm" /></td>
          <td>{{ item.anomaly_type ?? '—' }}</td>
          <td><TimestampDisplay :value="item.submitted_at" /></td>
          <td>
            <router-link :to="`/staff/exceptions/${item.exception_id}/review`" class="link-action">
              Review →
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!queue.loading" class="empty-msg">No exceptions pending review.</p>

    <PaginationControls :pagination="queue.pagination" @page="queue.loadExceptions({ page: $event })" />
  </div>
</template>

<style scoped>
.exception-queue-view { display: flex; flex-direction: column; gap: 1.25rem; }
.exception-queue-view h2 { margin: 0; }
.queue-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.queue-table th, .queue-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.queue-table th { background: #f5f5f5; font-weight: 600; }
.link-action { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.link-action:hover { text-decoration: underline; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
