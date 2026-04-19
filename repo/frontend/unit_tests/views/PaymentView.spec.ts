// FE-UNIT: PaymentView — form renders, duplicate submit blocked, success banner shown after submit.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import PaymentView from '@/views/candidate/orders/PaymentView.vue'
import { useOrderStore } from '@/stores/order'

vi.mock('@/services/orderApi', () => ({
  getOrder: vi.fn().mockResolvedValue({
    id: 'order-1', candidate_id: 'user-1', item_id: 'item-1',
    status: 'pending_payment', pricing_mode: 'fixed', agreed_price: null,
    auto_cancel_at: null, completed_at: null, canceled_at: null, cancellation_reason: null,
    created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z',
    events: [],
  }),
  listOrders: vi.fn().mockResolvedValue([]),
  createOrder: vi.fn(),
  cancelOrder: vi.fn(),
  confirmReceipt: vi.fn(),
  advanceOrder: vi.fn(),
  listServiceItems: vi.fn().mockResolvedValue([
    {
      id: 'item-1', item_code: 'SVC-1', name: 'NMAT Review', description: null,
      pricing_mode: 'fixed', fixed_price: '1200.00', is_capacity_limited: false,
      bargaining_enabled: false, available_slots: null,
    },
  ]),
}))

vi.mock('@/services/paymentApi', () => ({
  submitPaymentProof: vi.fn().mockResolvedValue({ id: 'pay-1', confirmed_by: null }),
  confirmPayment: vi.fn(),
  issueVoucher: vi.fn(),
  getVoucher: vi.fn(),
  addMilestone: vi.fn(),
  listMilestones: vi.fn(),
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/candidate/orders/:orderId/payment', component: PaymentView },
    { path: '/candidate/orders/:orderId', component: { template: '<div />' } },
  ],
})

describe('PaymentView', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    await router.push('/candidate/orders/order-1/payment')
    await router.isReady()
  })

  it('renders the payment view container', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="payment-view"]').exists()).toBe(true)
  })

  it('renders the payment form when order is loaded', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="payment-form"]').exists()).toBe(true)
  })

  it('pre-fills amount from catalog fixed_price when no agreed_price', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    const amountInput = wrapper.find('[data-testid="field-amount"]')
    expect((amountInput.element as HTMLInputElement).value).toBe('1200.00')
  })

  it('pre-fills amount from agreed_price when present', async () => {
    const { getOrder } = await import('@/services/orderApi')
    vi.mocked(getOrder).mockResolvedValueOnce({
      id: 'order-1', candidate_id: 'user-1', item_id: 'item-1',
      status: 'pending_payment', pricing_mode: 'bargaining', agreed_price: '980.00',
      auto_cancel_at: null, completed_at: null, canceled_at: null, cancellation_reason: null,
      created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-01T00:00:00Z',
      events: [],
    })
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    const amountInput = wrapper.find('[data-testid="field-amount"]')
    expect((amountInput.element as HTMLInputElement).value).toBe('980.00')
  })

  it('shows success banner after submission and hides form', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.submitPaymentProof = vi.fn().mockResolvedValue(true)
    await (wrapper.vm as any).submit()
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Payment proof submitted')
    expect(wrapper.find('[data-testid="payment-form"]').exists()).toBe(false)
  })

  it('prevents duplicate submission when already submitted', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    const submitSpy = vi.fn().mockResolvedValue(true)
    store.submitPaymentProof = submitSpy
    await (wrapper.vm as any).submit()
    await (wrapper.vm as any).submit()
    expect(submitSpy).toHaveBeenCalledTimes(1)
  })

  it('renders payment method select options', async () => {
    const wrapper = mount(PaymentView, { global: { plugins: [router] } })
    await flushPromises()
    const select = wrapper.find('[data-testid="field-payment-method"]')
    const options = select.findAll('option')
    expect(options.length).toBeGreaterThanOrEqual(4)
  })
})
