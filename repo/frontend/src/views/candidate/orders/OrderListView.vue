<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'
import StatusChip from '@/components/common/StatusChip.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import CountdownTimer from '@/components/common/CountdownTimer.vue'

const store = useOrderStore()

// BE OrderRead does not embed item_name/fixed_price. We fetch the catalog
// once and build an id→ServiceItem map for display name/pricing.
const itemMap = computed(() => {
  const m = new Map<string, { name: string; fixed_price: string | null }>()
  for (const it of store.items) m.set(it.id, { name: it.name, fixed_price: it.fixed_price })
  return m
})

onMounted(async () => {
  await Promise.all([store.loadOrders(), store.loadServiceItems()])
})
</script>

<template>
  <div class="order-list-view" data-testid="order-list-view">
    <div class="order-list-view__header">
      <h2>My Orders</h2>
      <router-link to="/candidate/orders/catalog" class="btn-primary btn-sm">
        Browse Services
      </router-link>
    </div>

    <LoadingSpinner v-if="store.loading" label="Loading orders…" />
    <BannerAlert v-if="store.error" type="error" :message="store.error" :dismissible="true" @dismiss="store.clearError()" />

    <EmptyState v-if="!store.loading && store.orders.length === 0" message="No orders yet. Browse services to place your first order." />

    <div v-for="order in store.orders" :key="order.id" class="order-card">
      <div class="order-card__head">
        <span class="order-card__name">{{ itemMap.get(order.item_id)?.name ?? '—' }}</span>
        <StatusChip :status="order.status" size="sm" />
      </div>

      <div class="order-card__details">
        <span>Catalog: <strong>{{ itemMap.get(order.item_id)?.fixed_price ?? '—' }}</strong></span>
        <span v-if="order.agreed_price">Agreed: <strong>{{ order.agreed_price }}</strong></span>
        <TimestampDisplay :value="order.created_at" />
      </div>

      <BannerAlert
        v-if="order.status === 'pending_payment'"
        type="warning"
        :message="`Payment due — auto-cancel at`"
      >
        <CountdownTimer :expires-at="order.auto_cancel_at" label="Auto-cancel in" />
      </BannerAlert>

      <BannerAlert
        v-if="order.status === 'refund_in_progress'"
        type="info"
        message="Refund is being processed."
      />

      <div class="order-card__actions">
        <router-link :to="`/candidate/orders/${order.id}`" class="link-action">View Details →</router-link>
        <router-link
          v-if="order.status === 'pending_payment' && order.pricing_mode === 'bargaining'"
          :to="`/candidate/orders/${order.id}/bargaining`"
          class="link-action"
        >
          Bargaining →
        </router-link>
        <router-link
          v-if="order.status === 'pending_payment'"
          :to="`/candidate/orders/${order.id}/payment`"
          class="link-action"
        >
          Submit Payment →
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.order-list-view { display: flex; flex-direction: column; gap: 1.25rem; }
.order-list-view__header { display: flex; align-items: center; justify-content: space-between; }
.order-list-view__header h2 { margin: 0; }
.order-card {
  border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.order-card__head { display: flex; align-items: center; justify-content: space-between; }
.order-card__name { font-weight: 600; }
.order-card__details { display: flex; gap: 1rem; font-size: 0.875rem; color: #555; flex-wrap: wrap; }
.order-card__actions { display: flex; gap: 1rem; flex-wrap: wrap; }
.link-action { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.link-action:hover { text-decoration: underline; }
.btn-primary { display: inline-block; padding: 0.5rem 1rem; background: #1565c0; color: white; border-radius: 4px; text-decoration: none; font-size: 0.875rem; }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; }
</style>
