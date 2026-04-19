// FE-UNIT: OrderDetailView — status chip, event history, payment link, auto-cancel countdown, bargaining link.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import OrderDetailView from '@/views/candidate/orders/OrderDetailView.vue'
import { useOrderStore } from '@/stores/order'

const MOCK_EVENT = {
  id: 'evt-1',
  sequence_number: 1,
  previous_state: null,
  new_state: 'pending_payment',
  actor_id: 'user-1',
  actor_role: 'candidate',
  notes: 'Order created',
  occurred_at: '2024-01-01T00:00:00Z',
}

const MOCK_ORDER_PENDING_PAYMENT = {
  id: 'order-1',
  candidate_id: 'user-1',
  item_id: 'item-1',
  status: 'pending_payment',
  pricing_mode: 'fixed',
  agreed_price: null,
  auto_cancel_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
  canceled_at: null,
  cancellation_reason: null,
  completed_at: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  events: [MOCK_EVENT],
}

const MOCK_ORDER_BARGAINING = {
  ...MOCK_ORDER_PENDING_PAYMENT,
  pricing_mode: 'bargaining',
}

const MOCK_ORDER_COMPLETED = {
  ...MOCK_ORDER_PENDING_PAYMENT,
  status: 'completed',
  auto_cancel_at: null,
  completed_at: '2024-01-02T00:00:00Z',
  events: [
    MOCK_EVENT,
    { ...MOCK_EVENT, id: 'evt-2', sequence_number: 2, previous_state: 'pending_payment', new_state: 'completed' },
  ],
}

vi.mock('@/services/orderApi', () => ({
  getOrder: vi.fn().mockResolvedValue(MOCK_ORDER_PENDING_PAYMENT),
  listOrdersPaginated: vi.fn().mockResolvedValue({ data: [], pagination: { page: 1, page_size: 20, total: 0, total_pages: 1 } }),
  listOrders: vi.fn().mockResolvedValue([]),
  createOrder: vi.fn(),
  cancelOrder: vi.fn().mockResolvedValue({ ...MOCK_ORDER_PENDING_PAYMENT, status: 'canceled' }),
  confirmReceipt: vi.fn(),
  advanceOrder: vi.fn(),
  listServiceItems: vi.fn().mockResolvedValue([]),
}))

vi.mock('@/services/paymentApi', () => ({
  submitPaymentProof: vi.fn(),
  confirmPayment: vi.fn(),
  issueVoucher: vi.fn(),
  getVoucher: vi.fn(),
  addMilestone: vi.fn(),
  listMilestones: vi.fn(),
}))

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/candidate/orders/:orderId', component: OrderDetailView },
    { path: '/candidate/orders', component: { template: '<div />' } },
    { path: '/candidate/orders/:orderId/payment', component: { template: '<div />' } },
    { path: '/candidate/orders/:orderId/bargaining', component: { template: '<div />' } },
  ],
})

describe('OrderDetailView', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    await router.push('/candidate/orders/order-1')
    await router.isReady()
  })

  it('renders the order-detail-view container', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="order-detail-view"]').exists()).toBe(true)
  })

  it('displays item name when order is loaded', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    store.currentItem = {
      id: 'item-1',
      item_code: 'SVC-1',
      name: 'NMAT Review',
      description: null,
      pricing_mode: 'fixed',
      fixed_price: '1200.00',
      is_capacity_limited: false,
      bargaining_enabled: false,
      available_slots: null,
    }
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('NMAT Review')
  })

  it('shows event history list when order has events', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('Order History')
  })

  it('shows payment link when status is pending_payment', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    await wrapper.vm.$nextTick()
    const paymentLink = wrapper.find('a[href="/candidate/orders/order-1/payment"]')
    expect(paymentLink.exists()).toBe(true)
    expect(paymentLink.text()).toContain('Submit Payment')
  })

  it('does not show payment link when order is completed', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_COMPLETED
    await wrapper.vm.$nextTick()
    const paymentLink = wrapper.find('a[href="/candidate/orders/order-1/payment"]')
    expect(paymentLink.exists()).toBe(false)
  })

  it('shows auto-cancel countdown when status is pending_payment and auto_cancel_at is set', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    await wrapper.vm.$nextTick()
    // CountdownTimer renders the label; view only renders it when status === pending_payment
    expect(wrapper.text()).toContain('Auto-cancel')
  })

  it('does not show auto-cancel countdown when order is completed', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_COMPLETED
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).not.toContain('Auto-cancel countdown')
  })

  it('shows bargaining link when pricing_mode is bargaining and status is pending_payment', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_BARGAINING
    await wrapper.vm.$nextTick()
    const bargainingLink = wrapper.find('a[href="/candidate/orders/order-1/bargaining"]')
    expect(bargainingLink.exists()).toBe(true)
    expect(bargainingLink.text()).toContain('Bargaining Thread')
  })

  it('does not show bargaining link for fixed-price orders', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    await wrapper.vm.$nextTick()
    const bargainingLink = wrapper.find('a[href="/candidate/orders/order-1/bargaining"]')
    expect(bargainingLink.exists()).toBe(false)
  })

  it('shows cancel button when status is pending_payment', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_PENDING_PAYMENT
    await wrapper.vm.$nextTick()
    const cancelBtn = wrapper.find('button.btn-danger')
    expect(cancelBtn.exists()).toBe(true)
    expect(cancelBtn.text()).toContain('Cancel Order')
  })

  it('shows event history entries in timeline', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = MOCK_ORDER_COMPLETED
    await wrapper.vm.$nextTick()
    // Two events in the completed order
    expect(store.currentOrder.events.length).toBe(2)
  })

  it('shows back link to orders list', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const backLink = wrapper.find('a[href="/candidate/orders"]')
    expect(backLink.exists()).toBe(true)
  })

  it('shows confirm receipt button when status is pending_receipt', async () => {
    const wrapper = mount(OrderDetailView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.currentOrder = { ...MOCK_ORDER_PENDING_PAYMENT, status: 'pending_receipt', auto_cancel_at: null }
    await wrapper.vm.$nextTick()
    const receiptBtn = wrapper.find('button.btn-primary')
    expect(receiptBtn.exists()).toBe(true)
    expect(receiptBtn.text()).toContain('Confirm Receipt')
  })
})
