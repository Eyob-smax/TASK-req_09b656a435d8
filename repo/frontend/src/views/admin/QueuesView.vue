<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import QueueBadge from '@/components/common/QueueBadge.vue'

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
  <div class="admin-queues-view" data-testid="admin-queues-view">
    <h2>Queue Overview</h2>
    <table class="queues-table">
      <thead><tr><th>Queue</th><th>Pending</th><th>Link</th></tr></thead>
      <tbody>
        <tr>
          <td>Document Review</td>
          <td><QueueBadge :count="queue.documents.length" /></td>
          <td><router-link to="/staff/documents">Open →</router-link></td>
        </tr>
        <tr>
          <td>Payment Confirmation</td>
          <td><QueueBadge :count="queue.payments.length" /></td>
          <td><router-link to="/staff/payments">Open →</router-link></td>
        </tr>
        <tr>
          <td>Order Fulfillment</td>
          <td><QueueBadge :count="queue.orders.length" /></td>
          <td><router-link to="/staff/orders">Open →</router-link></td>
        </tr>
        <tr>
          <td>Exception Review</td>
          <td><QueueBadge :count="queue.exceptions.length" /></td>
          <td><router-link to="/staff/exceptions">Open →</router-link></td>
        </tr>
        <tr>
          <td>After-Sales</td>
          <td><QueueBadge :count="queue.afterSales.length" /></td>
          <td><router-link to="/staff/after-sales">Open →</router-link></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.admin-queues-view { display: flex; flex-direction: column; gap: 1.25rem; }
.admin-queues-view h2 { margin: 0; }
.queues-table { border-collapse: collapse; font-size: 0.875rem; width: 100%; max-width: 480px; }
.queues-table th, .queues-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.queues-table th { background: #f5f5f5; font-weight: 600; }
</style>
