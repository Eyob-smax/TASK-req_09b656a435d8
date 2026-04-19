<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import { useAuthStore } from '@/stores/auth'
import QueueBadge from '@/components/common/QueueBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const auth = useAuthStore()
const queue = useQueueStore()

onMounted(async () => {
  await Promise.all([
    queue.loadDocuments(),
    queue.loadPayments(),
    queue.loadOrders(),
    queue.loadExceptions(),
    queue.loadAfterSales(),
  ])
})
</script>

<template>
  <div class="staff-dashboard" data-testid="staff-dashboard">
    <h2 class="staff-dashboard__title">Staff Dashboard</h2>
    <p class="staff-dashboard__user">Logged in as <strong>{{ auth.user?.full_name }}</strong> ({{ auth.role }})</p>

    <LoadingSpinner v-if="queue.loading" label="Loading queues…" />

    <div class="staff-dashboard__queues">
      <router-link to="/staff/documents" class="queue-card">
        <span class="queue-card__label">Document Review</span>
        <QueueBadge :count="queue.documents.length" label="pending" />
      </router-link>

      <router-link to="/staff/payments" class="queue-card">
        <span class="queue-card__label">Payment Confirmation</span>
        <QueueBadge :count="queue.payments.length" label="pending" />
      </router-link>

      <router-link to="/staff/orders" class="queue-card">
        <span class="queue-card__label">Order Fulfillment</span>
        <QueueBadge :count="queue.orders.length" label="pending" />
      </router-link>

      <router-link to="/staff/exceptions" class="queue-card">
        <span class="queue-card__label">Exception Review</span>
        <QueueBadge :count="queue.exceptions.length" label="pending" />
      </router-link>

      <router-link to="/staff/after-sales" class="queue-card">
        <span class="queue-card__label">After-Sales</span>
        <QueueBadge :count="queue.afterSales.length" label="pending" />
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.staff-dashboard { display: flex; flex-direction: column; gap: 1.25rem; }
.staff-dashboard__title { margin: 0; font-size: 1.25rem; }
.staff-dashboard__user { margin: 0; color: #555; font-size: 0.875rem; }
.staff-dashboard__queues {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem;
}
.queue-card {
  display: flex; align-items: center; justify-content: space-between;
  border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem;
  text-decoration: none; color: inherit; transition: box-shadow 0.15s;
}
.queue-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.queue-card__label { font-size: 0.9rem; font-weight: 500; color: #37474f; }
</style>
