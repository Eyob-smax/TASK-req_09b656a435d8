<script setup lang="ts">
import { onMounted } from 'vue'
import { useQueueStore } from '@/stores/queue'
import { useOrderStore } from '@/stores/order'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import PaginationControls from '@/components/common/PaginationControls.vue'

const queue = useQueueStore()
const orderStore = useOrderStore()
const confirmedOrderId = ref<string | null>(null)

import { ref } from 'vue'

onMounted(async () => {
  await queue.loadPayments()
})

async function confirm(orderId: string, amount: string, paymentMethod: string, referenceNumber: string | null): Promise<void> {
  const { confirmPayment } = await import('@/services/paymentApi')
  try {
    await confirmPayment(orderId, {
      amount,
      payment_method: paymentMethod,
      reference_number: referenceNumber,
    })
    confirmedOrderId.value = orderId
    await queue.loadPayments()
  } catch (e) {
    orderStore.error = (e as Error).message
  }
}
</script>

<template>
  <div class="payment-queue-view" data-testid="payment-queue-view">
    <h2>Payment Confirmation Queue</h2>

    <BannerAlert v-if="confirmedOrderId" type="success" :message="`Order ${confirmedOrderId} payment confirmed.`" :dismissible="true" @dismiss="confirmedOrderId = null" />
    <BannerAlert v-if="orderStore.error" type="error" :message="orderStore.error" :dismissible="true" @dismiss="orderStore.clearError()" />

    <table v-if="queue.payments.length > 0" class="queue-table">
      <thead>
        <tr><th>Order ID</th><th>Service</th><th>Amount</th><th>Method</th><th>Ref #</th><th>Submitted</th><th>Actions</th></tr>
      </thead>
      <tbody>
        <tr v-for="item in queue.payments" :key="item.order_id">
          <td><code>{{ item.order_id.slice(0, 8) }}…</code></td>
          <td>{{ item.item_name }}</td>
          <td><strong>{{ item.amount }}</strong></td>
          <td>{{ item.payment_method }}</td>
          <td><code>{{ item.reference_number }}</code></td>
          <td><TimestampDisplay :value="item.submitted_at" /></td>
          <td>
            <button type="button" class="btn-confirm" @click="confirm(item.order_id, item.amount, item.payment_method, item.reference_number)">Confirm</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!queue.loading" class="empty-msg">No payments awaiting confirmation.</p>

    <PaginationControls :pagination="queue.pagination" @page="queue.loadPayments({ page: $event })" />
  </div>
</template>

<style scoped>
.payment-queue-view { display: flex; flex-direction: column; gap: 1.25rem; }
.payment-queue-view h2 { margin: 0; }
.queue-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.queue-table th, .queue-table td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #e0e0e0; text-align: left; }
.queue-table th { background: #f5f5f5; font-weight: 600; }
.btn-confirm { padding: 0.25rem 0.75rem; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
