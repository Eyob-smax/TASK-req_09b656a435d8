<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import DataTable from '@/components/common/DataTable.vue'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'
import type { DocumentQueueItem } from '@/types/queue'

const queue = useQueueStore()

onMounted(async () => {
  await queue.loadDocuments()
})
</script>

<template>
  <div class="document-queue-view" data-testid="document-queue-view">
    <h2>Document Review Queue</h2>

    <table v-if="queue.documents.length > 0" class="queue-table">
      <thead>
        <tr>
          <th>Document Type</th>
          <th>Requirement</th>
          <th>Status</th>
          <th>Submitted</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in queue.documents" :key="item.document_id">
          <td>{{ item.document_type }}</td>
          <td>{{ item.requirement_code ?? '—' }}</td>
          <td><StatusChip :status="item.current_status" size="sm" /></td>
          <td><TimestampDisplay :value="item.submitted_at" /></td>
          <td>
            <router-link
              :to="{ path: `/staff/documents/${item.document_id}/review`, query: { candidateId: item.candidate_id } }"
              class="link-action"
            >
              Review →
            </router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!queue.loading" class="empty-msg">No documents pending review.</p>

    <PaginationControls :pagination="queue.pagination" @page="queue.loadDocuments({ page: $event })" />
  </div>
</template>

<style scoped>
.document-queue-view { display: flex; flex-direction: column; gap: 1.25rem; }
.document-queue-view h2 { margin: 0; }
.queue-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.queue-table th, .queue-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.queue-table th { background: #f5f5f5; font-weight: 600; }
.link-action { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.link-action:hover { text-decoration: underline; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
