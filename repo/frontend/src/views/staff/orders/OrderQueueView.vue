<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const queue = useQueueStore()

onMounted(async () => {
  await queue.loadOrders()
})
</script>

<template>
  <div class="order-queue-view" data-testid="order-queue-view">
    <h2>Order Fulfillment Queue</h2>

    <table v-if="queue.orders.length > 0" class="queue-table">
      <thead>
        <tr><th>Order ID</th><th>Service</th><th>Status</th><th>Agreed Price</th><th>Updated</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in queue.orders" :key="item.order_id">
          <td><code>{{ item.order_id.slice(0, 8) }}…</code></td>
          <td>{{ item.item_name }}</td>
          <td><StatusChip :status="item.status" size="sm" /></td>
          <td>{{ item.agreed_price ?? '—' }}</td>
          <td><TimestampDisplay :value="item.updated_at" /></td>
          <td>
            <router-link :to="`/staff/orders/${item.order_id}`" class="link-action">Manage →</router-link>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!queue.loading" class="empty-msg">No orders pending fulfillment.</p>

    <PaginationControls :pagination="queue.pagination" @page="queue.loadOrders({ page: $event })" />
  </div>
</template>

<style scoped>
.order-queue-view { display: flex; flex-direction: column; gap: 1.25rem; }
.order-queue-view h2 { margin: 0; }
.queue-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.queue-table th, .queue-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.queue-table th { background: #f5f5f5; font-weight: 600; }
.link-action { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.link-action:hover { text-decoration: underline; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
