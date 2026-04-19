<script setup lang="ts">
import { onMounted } from 'vue'
import { useAttendanceStore } from '@/stores/attendance'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const store = useAttendanceStore()

onMounted(async () => {
  await store.loadExceptions()
})
</script>

<template>
  <div class="exception-list-view" data-testid="exception-list-view">
    <div class="exception-list-view__header">
      <h2>Attendance Exceptions</h2>
      <router-link to="/candidate/attendance/new" class="btn-primary btn-sm">
        + File Exception
      </router-link>
    </div>

    <LoadingSpinner v-if="store.loading" label="Loading exceptions…" />
    <BannerAlert v-if="store.error" type="error" :message="store.error" :dismissible="true" @dismiss="store.clearError()" />

    <EmptyState v-if="!store.loading && store.exceptions.length === 0" message="No attendance exceptions filed." />

    <div v-for="exc in store.exceptions" :key="exc.id" class="exception-card">
      <div class="exception-card__head">
        <StatusChip :status="exc.status" />
        <span class="exception-card__stage">Stage: {{ exc.current_stage }}</span>
        <TimestampDisplay :value="exc.created_at" />
      </div>
      <p class="exception-card__statement">{{ exc.candidate_statement }}</p>
      <router-link :to="`/candidate/attendance/${exc.id}`" class="link-action">View & Upload Proof →</router-link>
    </div>

    <PaginationControls :pagination="store.pagination" @page="store.loadExceptions({ page: $event })" />
  </div>
</template>

<style scoped>
.exception-list-view { display: flex; flex-direction: column; gap: 1.25rem; }
.exception-list-view__header { display: flex; align-items: center; justify-content: space-between; }
.exception-list-view__header h2 { margin: 0; }
.exception-card { border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.exception-card__head { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.exception-card__stage { font-size: 0.8rem; color: #777; }
.exception-card__statement { margin: 0; font-size: 0.875rem; color: #333; }
.link-action { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.link-action:hover { text-decoration: underline; }
.btn-primary { display: inline-block; padding: 0.5rem 1rem; background: #1565c0; color: white; border-radius: 4px; text-decoration: none; font-size: 0.875rem; }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; }
</style>
