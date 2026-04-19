<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useOrderStore } from '@/stores/order'
import { issueVoucher, addMilestone } from '@/services/paymentApi'
import StatusChip from '@/components/common/StatusChip.vue'
import TimelineList from '@/components/common/TimelineList.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import { ref, computed } from 'vue'
import type { TimelineEntry } from '@/components/common/TimelineList.vue'

const route = useRoute()
const store = useOrderStore()
const orderId = route.params.orderId as string
const voucherNotes = ref('')
const milestoneType = ref('')
const notification = ref<string | null>(null)
const bargainingStore = (await import('@/stores/bargaining')).useBargainingStore()

const timeline = computed<TimelineEntry[]>(() => {
  if (!store.currentOrder?.events) return []
  return store.currentOrder.events.map((e) => ({
    id: e.id,
    label: `${e.previous_state ?? '—'} → ${e.new_state}`,
    description: e.notes ?? null,
    timestamp: e.occurred_at,
    actor: e.actor_role,
  }))
})

onMounted(async () => {
  await store.loadOrder(orderId)
  if (store.currentOrder?.pricing_mode === 'bargaining') {
    await bargainingStore.loadThread(orderId)
  }
})

async function advance(): Promise<void> {
  await store.advanceOrder(orderId)
  notification.value = 'Order advanced to pending receipt.'
}

async function handleIssueVoucher(): Promise<void> {
  try {
    await issueVoucher(orderId, { notes: voucherNotes.value || null })
    notification.value = 'Voucher issued.'
  } catch (e) {
    store.error = (e as Error).message
  }
}

async function handleAddMilestone(): Promise<void> {
  if (!milestoneType.value) return
  try {
    await addMilestone(orderId, { milestone_type: milestoneType.value })
    notification.value = 'Milestone recorded.'
    milestoneType.value = ''
  } catch (e) {
    store.error = (e as Error).message
  }
}

async function handleAcceptOffer(offerId: string): Promise<void> {
  await bargainingStore.acceptOffer(orderId, offerId)
  await store.loadOrder(orderId)
}

async function handleCounterOffer(): Promise<void> {
  const amount = prompt('Enter counter amount:')
  if (!amount) return
  await bargainingStore.counterOffer(orderId, amount)
}
// Payment confirmation lives on /staff/orders/payment-queue (PaymentQueueView)
// where each pending proof is listed with the submitted amount + method (the
// fields required by BE PaymentConfirmRequest). OrderRead does not embed
// payment records, so this view intentionally does not surface a confirm
// button — link candidates to the queue instead.
</script>

<template>
  <div class="staff-order-detail" data-testid="staff-order-detail">
    <div class="staff-order-detail__header">
      <h2>Order Detail (Staff)</h2>
      <router-link to="/staff/orders" class="back-link">← Order Queue</router-link>
    </div>

    <LoadingSpinner v-if="store.loading" label="Loading…" />
    <BannerAlert v-if="notification" type="success" :message="notification" :dismissible="true" @dismiss="notification = null" />
    <BannerAlert v-if="store.error" type="error" :message="store.error" :dismissible="true" @dismiss="store.clearError()" />

    <template v-if="store.currentOrder">
      <div class="staff-order-detail__summary">
        <h3>{{ store.currentItem?.name ?? 'Order' }}</h3>
        <StatusChip :status="store.currentOrder.status" />
        <table class="detail-table">
          <tr><th>Catalog Price</th><td>{{ store.currentItem?.fixed_price ?? '—' }}</td></tr>
          <tr><th>Agreed Price</th><td>{{ store.currentOrder.agreed_price ?? '—' }}</td></tr>
          <tr><th>Pricing Mode</th><td>{{ store.currentOrder.pricing_mode }}</td></tr>
          <tr v-if="store.currentOrder.canceled_at">
            <th>Canceled</th><td><TimestampDisplay :value="store.currentOrder.canceled_at" /></td>
          </tr>
          <tr v-if="store.currentOrder.cancellation_reason">
            <th>Cancel Reason</th><td>{{ store.currentOrder.cancellation_reason }}</td>
          </tr>
        </table>
      </div>

      <!-- Bargaining actions -->
      <section v-if="bargainingStore.thread && store.currentOrder.pricing_mode === 'bargaining'" class="bargaining-panel">
        <h3>Bargaining</h3>
        <p>Status: <StatusChip :status="bargainingStore.thread.status" size="sm" /></p>
        <div v-if="bargainingStore.thread.offers.length > 0">
          <table class="offers-table">
            <thead><tr><th>#</th><th>Amount</th><th>Outcome</th></tr></thead>
            <tbody>
              <tr v-for="offer in bargainingStore.thread.offers" :key="offer.id">
                <td>{{ offer.offer_number }}</td>
                <td>{{ offer.amount }}</td>
                <td>
                  <StatusChip :status="offer.outcome" size="sm" />
                  <button
                    v-if="offer.outcome === 'pending'"
                    type="button"
                    class="btn-sm-green"
                    @click="handleAcceptOffer(offer.id)"
                  >Accept</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <button
          v-if="bargainingStore.thread.status === 'open' && bargainingStore.thread.counter_count === 0"
          type="button"
          class="btn-secondary"
          @click="handleCounterOffer"
        >
          Counter Offer
        </button>
      </section>

      <!-- Payment confirmation lives on the dedicated queue view. -->
      <section v-if="store.currentOrder.status === 'pending_payment'" class="payment-confirm-panel">
        <h3>Payment</h3>
        <p>
          Confirm submitted payment proofs in the
          <router-link to="/staff/orders/payment-queue">payment queue</router-link>.
        </p>
      </section>

      <!-- Advance order -->
      <div class="staff-order-detail__actions">
        <button
          v-if="store.currentOrder.status === 'pending_fulfillment'"
          type="button"
          class="btn-primary"
          :disabled="store.submitting"
          @click="advance"
        >
          Advance to Pending Receipt
        </button>
      </div>

      <!-- Voucher + milestones -->
      <section v-if="store.currentOrder.status === 'pending_fulfillment'" class="voucher-section">
        <h3>Issue Voucher</h3>
        <div class="inline-form">
          <input v-model="voucherNotes" type="text" placeholder="Notes (optional)" />
          <button type="button" class="btn-secondary" @click="handleIssueVoucher">Issue</button>
        </div>
      </section>

      <section v-if="store.currentOrder.status === 'pending_fulfillment'" class="milestone-section">
        <h3>Add Milestone</h3>
        <div class="inline-form">
          <input v-model="milestoneType" type="text" placeholder="Milestone type" required />
          <button type="button" class="btn-secondary" @click="handleAddMilestone" :disabled="!milestoneType">Add</button>
        </div>
      </section>

      <section class="order-detail__timeline">
        <h3>Order History</h3>
        <TimelineList :entries="timeline" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.staff-order-detail { display: flex; flex-direction: column; gap: 1.25rem; }
.staff-order-detail__header { display: flex; align-items: center; justify-content: space-between; }
.staff-order-detail__header h2 { margin: 0; }
.back-link { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.staff-order-detail__summary { display: flex; flex-direction: column; gap: 0.5rem; }
.staff-order-detail__summary h3 { margin: 0; }
.detail-table { border-collapse: collapse; font-size: 0.875rem; }
.detail-table th, .detail-table td { padding: 0.3rem 0.6rem; border-bottom: 1px solid #e0e0e0; }
.detail-table th { width: 120px; color: #555; font-weight: 500; }
.bargaining-panel, .payment-confirm-panel, .voucher-section, .milestone-section { border: 1px solid #e0e0e0; border-radius: 6px; padding: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.bargaining-panel h3, .payment-confirm-panel h3, .voucher-section h3, .milestone-section h3 { margin: 0; font-size: 1rem; }
.offers-table { border-collapse: collapse; font-size: 0.875rem; width: 100%; }
.offers-table th, .offers-table td { padding: 0.3rem 0.5rem; border-bottom: 1px solid #e0e0e0; }
.staff-order-detail__actions { display: flex; gap: 0.75rem; }
.inline-form { display: flex; gap: 0.5rem; align-items: center; }
.inline-form input { padding: 0.35rem 0.5rem; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 0.875rem; flex: 1; }
.btn-primary { padding: 0.5rem 1rem; background: #1565c0; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-primary:disabled { opacity: 0.6; }
.btn-secondary { padding: 0.4rem 0.75rem; background: white; color: #1565c0; border: 1px solid #1565c0; border-radius: 4px; cursor: pointer; font-size: 0.875rem; }
.btn-sm-green { padding: 0.15rem 0.5rem; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75rem; margin-left: 0.25rem; }
.order-detail__timeline h3 { margin: 0 0 0.5rem; font-size: 1rem; }
</style>
