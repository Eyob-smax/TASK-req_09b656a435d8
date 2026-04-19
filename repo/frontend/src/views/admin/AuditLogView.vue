<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '@/stores/admin'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const admin = useAdminStore()

const filterEventType = ref('')
const filterActorId = ref('')
const filterOutcome = ref('')
const filterFromDate = ref('')
const filterToDate = ref('')
const currentPage = ref(1)

onMounted(async () => {
  await admin.loadAuditLog({ page: 1, page_size: 20 })
})

async function applyFilters() {
  currentPage.value = 1
  await admin.searchAuditLog({
    event_type: filterEventType.value || undefined,
    actor_id: filterActorId.value || undefined,
    outcome: filterOutcome.value || undefined,
    from_date: filterFromDate.value || undefined,
    to_date: filterToDate.value || undefined,
  } as Record<string, string>)
}

async function goToPage(page: number) {
  currentPage.value = page
  await admin.loadAuditLog({ page, page_size: 20 })
}
</script>

<template>
  <div class="audit-log-view" data-testid="audit-log-view">
    <h2>Audit Log</h2>

    <form class="audit-filters" data-testid="audit-filter-form" @submit.prevent="applyFilters">
      <input
        v-model="filterEventType"
        placeholder="Event type"
        class="filter-input"
        data-testid="filter-event-type"
      />
      <input
        v-model="filterActorId"
        placeholder="Actor ID"
        class="filter-input"
        data-testid="filter-actor-id"
      />
      <input
        v-model="filterOutcome"
        placeholder="Outcome"
        class="filter-input"
        data-testid="filter-outcome"
      />
      <input
        v-model="filterFromDate"
        type="datetime-local"
        class="filter-input"
        data-testid="filter-from-date"
      />
      <input
        v-model="filterToDate"
        type="datetime-local"
        class="filter-input"
        data-testid="filter-to-date"
      />
      <button type="submit" class="filter-btn" data-testid="audit-search-btn">Search</button>
    </form>

    <LoadingSpinner v-if="admin.loading" label="Loading audit log…" />
    <EmptyState v-else-if="admin.auditLog.length === 0" message="No audit entries found." />
    <template v-else>
      <p class="audit-count">{{ admin.auditTotal }} total entries</p>
      <table class="audit-table">
        <thead>
          <tr>
            <th>Event</th><th>Actor</th><th>Role</th>
            <th>Resource</th><th>Outcome</th><th>At</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in admin.auditLog" :key="entry.id">
            <td>{{ entry.event_type }}</td>
            <td><code>{{ entry.actor_id ? entry.actor_id.slice(0, 8) : '—' }}</code></td>
            <td>{{ entry.actor_role ?? '—' }}</td>
            <td>{{ entry.resource_type ?? '—' }}</td>
            <td>{{ entry.outcome }}</td>
            <td><TimestampDisplay :value="entry.occurred_at" /></td>
          </tr>
        </tbody>
      </table>
      <PaginationControls
        :current-page="currentPage"
        :total-pages="Math.ceil(admin.auditTotal / 20)"
        @page-change="goToPage"
      />
    </template>
  </div>
</template>

<style scoped>
.audit-log-view { display: flex; flex-direction: column; gap: 1.25rem; }
.audit-log-view h2 { margin: 0; }
.audit-filters { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.filter-input { border: 1px solid #ccc; border-radius: 4px; padding: 0.3rem 0.5rem; font-size: 0.85rem; }
.filter-btn { padding: 0.3rem 0.75rem; background: #1565c0; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
.audit-count { font-size: 0.8rem; color: #666; margin: 0; }
.audit-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.audit-table th, .audit-table td { padding: 0.4rem 0.6rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.audit-table th { background: #f5f5f5; font-weight: 600; }
</style>
