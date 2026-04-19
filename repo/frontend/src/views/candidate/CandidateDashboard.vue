<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useCandidateStore } from '@/stores/candidate'
import { useOrderStore } from '@/stores/order'
import StatusChip from '@/components/common/StatusChip.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TimestampDisplay from '@/components/common/TimestampDisplay.vue'

const auth = useAuthStore()
const candidateStore = useCandidateStore()
const orderStore = useOrderStore()

const candidateId = computed(() => auth.candidateId ?? '')

const itemMap = computed(() => {
  const m = new Map<string, string>()
  for (const it of orderStore.items) m.set(it.id, it.name)
  return m
})

onMounted(async () => {
  await orderStore.loadServiceItems()
  if (!candidateId.value) return
  await Promise.all([
    candidateStore.loadProfile(candidateId.value),
    candidateStore.loadChecklist(candidateId.value),
    orderStore.loadOrders(),
  ])
})

const pendingOrderCount = computed(
  () => orderStore.orders.filter((o) => o.status === 'pending_payment').length,
)
const checklistPending = computed(
  () => candidateStore.checklist.filter((c) => !c.status || c.status === 'needs_resubmission').length,
)
</script>

<template>
  <div class="dashboard" data-testid="candidate-dashboard">
    <h2 class="dashboard__title">
      Welcome back, {{ auth.user?.full_name ?? auth.user?.username }}
    </h2>

    <div class="dashboard__cards">
      <router-link to="/candidate/profile" class="dashboard__card">
        <h3>Profile</h3>
        <p>{{ candidateStore.profile ? 'Complete' : 'Not set up' }}</p>
      </router-link>

      <router-link to="/candidate/documents" class="dashboard__card" :class="{ 'dashboard__card--alert': checklistPending > 0 }">
        <h3>Documents</h3>
        <p>{{ checklistPending > 0 ? `${checklistPending} item(s) need attention` : 'All up to date' }}</p>
      </router-link>

      <router-link to="/candidate/orders" class="dashboard__card" :class="{ 'dashboard__card--alert': pendingOrderCount > 0 }">
        <h3>Orders</h3>
        <p>{{ pendingOrderCount > 0 ? `${pendingOrderCount} order(s) awaiting payment` : orderStore.orders.length + ' order(s)' }}</p>
      </router-link>

      <router-link to="/candidate/attendance" class="dashboard__card">
        <h3>Attendance</h3>
        <p>View exceptions &amp; proofs</p>
      </router-link>
    </div>

    <section v-if="orderStore.orders.length > 0" class="dashboard__section">
      <h3>Recent Orders</h3>
      <table class="dashboard__orders">
        <thead>
          <tr><th>Service</th><th>Status</th><th>Created</th></tr>
        </thead>
        <tbody>
          <tr v-for="order in orderStore.orders.slice(0, 5)" :key="order.id">
            <td>
              <router-link :to="`/candidate/orders/${order.id}`">{{ itemMap.get(order.item_id) ?? '—' }}</router-link>
            </td>
            <td><StatusChip :status="order.status" size="sm" /></td>
            <td><TimestampDisplay :value="order.created_at" /></td>
          </tr>
        </tbody>
      </table>
    </section>

    <LoadingSpinner v-if="candidateStore.loading || orderStore.loading" label="Loading dashboard…" />
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 1.5rem; }
.dashboard__title { margin: 0; font-size: 1.25rem; }
.dashboard__cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.dashboard__card {
  border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem;
  text-decoration: none; color: inherit; transition: box-shadow 0.15s;
}
.dashboard__card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.dashboard__card--alert { border-color: #f59e0b; background: #fef3c7; }
.dashboard__card h3 { margin: 0 0 0.25rem; font-size: 0.95rem; color: #1565c0; }
.dashboard__card p { margin: 0; font-size: 0.85rem; color: #555; }
.dashboard__section h3 { font-size: 1rem; margin: 0 0 0.5rem; }
.dashboard__orders { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.dashboard__orders th, .dashboard__orders td {
  padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #e0e0e0;
}
.dashboard__orders th { background: #f5f5f5; font-weight: 600; }
</style>
