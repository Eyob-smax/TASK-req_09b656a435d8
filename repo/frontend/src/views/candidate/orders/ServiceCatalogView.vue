<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOrderStore } from '@/stores/order'
import { useSessionStore } from '@/stores/session'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import BannerAlert from '@/components/common/BannerAlert.vue'
import type { ServiceItem, PricingMode } from '@/types/order'

const store = useOrderStore()
const session = useSessionStore()
const router = useRouter()
const placing = ref(false)
const placingError = ref<string | null>(null)

onMounted(async () => {
  await store.loadServiceItems()
})

async function order(item: ServiceItem): Promise<void> {
  placing.value = true
  placingError.value = null
  const pricingMode: PricingMode = (
    item.pricing_mode === 'bargaining' &&
    item.bargaining_enabled &&
    session.bargainingEnabled
  ) ? 'bargaining' : 'fixed'

  const result = await store.placeOrder({ item_id: item.id, pricing_mode: pricingMode })
  if (result) {
    await router.push(`/candidate/orders/${result.id}`)
  } else {
    placingError.value = store.error ?? 'Failed to place order.'
  }
  placing.value = false
}
</script>

<template>
  <div class="catalog-view" data-testid="service-catalog-view">
    <div class="catalog-view__header">
      <h2>Service Catalog</h2>
      <router-link to="/candidate/orders" class="back-link">← My Orders</router-link>
    </div>

    <LoadingSpinner v-if="store.loading" label="Loading catalog…" />
    <BannerAlert v-if="placingError" type="error" :message="placingError" :dismissible="true" @dismiss="placingError = null" />

    <div class="catalog-grid">
      <article v-for="item in store.items" :key="item.id" class="catalog-card">
        <h3 class="catalog-card__name">{{ item.name }}</h3>
        <p v-if="item.description" class="catalog-card__desc">{{ item.description }}</p>

        <div class="catalog-card__meta">
          <span class="catalog-card__price">{{ item.fixed_price ?? '—' }}</span>
          <span class="catalog-card__mode">
            {{ item.pricing_mode === 'bargaining' && item.bargaining_enabled ? 'Negotiable' : 'Fixed price' }}
          </span>
        </div>

        <div v-if="item.is_capacity_limited" class="catalog-card__capacity">
          Slots available: {{ item.available_slots ?? 0 }}
        </div>

        <button
          type="button"
          class="btn-primary"
          :disabled="placing || (item.is_capacity_limited && (item.available_slots ?? 0) === 0)"
          data-testid="order-btn"
          @click="order(item)"
        >
          {{ placing ? 'Placing order…' : 'Order' }}
        </button>

        <p v-if="item.is_capacity_limited && (item.available_slots ?? 0) === 0" class="catalog-card__no-slots">
          No slots available
        </p>
      </article>
    </div>

    <p v-if="!store.loading && store.items.length === 0" class="empty-msg">
      No services available at this time.
    </p>
  </div>
</template>

<style scoped>
.catalog-view { display: flex; flex-direction: column; gap: 1.25rem; }
.catalog-view__header { display: flex; align-items: center; justify-content: space-between; }
.catalog-view__header h2 { margin: 0; }
.back-link { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.catalog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; }
.catalog-card {
  border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.25rem;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.catalog-card--inactive { opacity: 0.5; }
.catalog-card__name { margin: 0; font-size: 1rem; }
.catalog-card__desc { margin: 0; font-size: 0.8rem; color: #555; }
.catalog-card__meta { display: flex; justify-content: space-between; align-items: center; }
.catalog-card__price { font-weight: 700; color: #1565c0; }
.catalog-card__mode { font-size: 0.75rem; background: #e3f2fd; color: #1565c0; padding: 0.1rem 0.4rem; border-radius: 3px; }
.catalog-card__capacity { font-size: 0.8rem; color: #555; }
.catalog-card__no-slots { font-size: 0.75rem; color: #ef4444; margin: 0; }
.btn-primary { padding: 0.5rem 1rem; background: #1565c0; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.empty-msg { color: #888; font-size: 0.875rem; }
</style>
