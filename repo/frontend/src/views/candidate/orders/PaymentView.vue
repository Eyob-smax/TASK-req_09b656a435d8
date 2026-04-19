<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useOrderStore } from '@/stores/order'
import BannerAlert from '@/components/common/BannerAlert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import type { PaymentProofSubmit } from '@/types/order'

const route = useRoute()
const router = useRouter()
const store = useOrderStore()
const orderId = route.params.orderId as string
const submitted = ref(false)

const form = reactive<PaymentProofSubmit>({
  payment_method: '',
  reference_number: '',
  amount: '',
  notes: null,
})

onMounted(async () => {
  await store.loadOrder(orderId)
  const agreed = store.currentOrder?.agreed_price
  const fixed = store.currentItem?.fixed_price
  if (agreed) {
    form.amount = agreed
  } else if (fixed) {
    form.amount = fixed
  }
})

async function submit(): Promise<void> {
  if (submitted.value) return // prevent duplicate submit
  const ok = await store.submitPaymentProof(orderId, { ...form })
  if (ok) {
    submitted.value = true
  }
}
</script>

<template>
  <div class="payment-view" data-testid="payment-view">
    <div class="payment-view__header">
      <h2>Submit Payment Proof</h2>
      <router-link :to="`/candidate/orders/${orderId}`" class="back-link">← Order Detail</router-link>
    </div>

    <LoadingSpinner v-if="store.loading" label="Loading order…" />
    <BannerAlert v-if="store.error" type="error" :message="store.error" :dismissible="true" @dismiss="store.clearError()" />

    <BannerAlert
      v-if="submitted"
      type="success"
      message="Payment proof submitted. Awaiting reviewer confirmation."
    />

    <template v-if="!submitted && store.currentOrder">
      <p class="payment-view__info">
        Order: <strong>{{ store.currentItem?.name ?? '—' }}</strong> ·
        Amount: <strong>{{ store.currentOrder.agreed_price ?? store.currentItem?.fixed_price ?? '—' }}</strong>
      </p>

      <form class="payment-form" @submit.prevent="submit" data-testid="payment-form">
        <label class="payment-form__field">
          Payment Method *
          <select v-model="form.payment_method" required data-testid="field-payment-method">
            <option value="">Select…</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="online_payment">Online Payment</option>
            <option value="cash">Cash</option>
            <option value="check">Check</option>
          </select>
        </label>

        <label class="payment-form__field">
          Reference Number *
          <input v-model="form.reference_number" type="text" required data-testid="field-reference-number" placeholder="Transaction / receipt number" />
        </label>

        <label class="payment-form__field">
          Amount *
          <input v-model="form.amount" type="number" min="0" step="0.01" required data-testid="field-amount" />
        </label>

        <label class="payment-form__field">
          Notes
          <textarea v-model="form.notes" rows="2" data-testid="field-notes" />
        </label>

        <button
          type="submit"
          class="btn-primary"
          :disabled="store.submitting || submitted"
          data-testid="payment-submit"
        >
          {{ store.submitting ? 'Submitting…' : 'Submit Payment Proof' }}
        </button>
      </form>
    </template>
  </div>
</template>

<style scoped>
.payment-view { display: flex; flex-direction: column; gap: 1.25rem; max-width: 480px; }
.payment-view__header { display: flex; align-items: center; justify-content: space-between; }
.payment-view__header h2 { margin: 0; }
.back-link { font-size: 0.875rem; color: #1565c0; text-decoration: none; }
.payment-view__info { font-size: 0.9rem; color: #555; margin: 0; }
.payment-form { display: flex; flex-direction: column; gap: 0.875rem; }
.payment-form__field { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.875rem; }
.payment-form__field input, .payment-form__field select, .payment-form__field textarea {
  padding: 0.4rem 0.5rem; border: 1px solid #bdbdbd; border-radius: 4px; font-size: 0.875rem;
}
.btn-primary { padding: 0.5rem 1.25rem; background: #1565c0; color: white; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
