// FE-UNIT: OrderListView — renders list, empty state, order cards with status chip and item name, detail/payment/bargaining links.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import OrderListView from '@/views/candidate/orders/OrderListView.vue'
import { useOrderStore } from '@/stores/order'

const MOCK_PAGINATION = { page: 1, page_size: 20, total: 1, total_pages: 1 }

const MOCK_ORDER_PENDING = {
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
  events: [],
}

const MOCK_ORDER_BARGAINING = {
  ...MOCK_ORDER_PENDING,
  id: 'order-2',
  pricing_mode: 'bargaining',
}

const MOCK_ITEMS = [
  {
    id: 'item-1',
    item_code: 'SVC-1',
    name: 'NMAT Review',
    description: null,
    pricing_mode: 'fixed',
    fixed_price: '1200.00',
    is_capacity_limited: false,
    bargaining_enabled: false,
    available_slots: null,
  },
  {
    id: 'item-2',
    item_code: 'SVC-2',
    name: 'Campus Tour',
    description: null,
    pricing_mode: 'bargaining',
    fixed_price: '900.00',
    is_capacity_limited: false,
    bargaining_enabled: true,
    available_slots: null,
  },
]

vi.mock('@/services/orderApi', () => ({
  listOrdersPaginated: vi.fn().mockResolvedValue({ data: [MOCK_ORDER_PENDING], pagination: MOCK_PAGINATION }),
  listOrders: vi.fn().mockResolvedValue([]),
  getOrder: vi.fn(),
  createOrder: vi.fn(),
  cancelOrder: vi.fn(),
  confirmReceipt: vi.fn(),
  advanceOrder: vi.fn(),
  listServiceItems: vi.fn().mockResolvedValue(MOCK_ITEMS),
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
    { path: '/candidate/orders', component: OrderListView },
    { path: '/candidate/orders/:orderId', component: { template: '<div />' } },
    { path: '/candidate/orders/:orderId/payment', component: { template: '<div />' } },
    { path: '/candidate/orders/:orderId/bargaining', component: { template: '<div />' } },
    { path: '/candidate/orders/catalog', component: { template: '<div />' } },
  ],
})

describe('OrderListView', () => {
  beforeEach(async () => {
    setActivePinia(createPinia())
    await router.push('/candidate/orders')
    await router.isReady()
  })

  it('renders the order-list-view container', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    expect(wrapper.find('[data-testid="order-list-view"]').exists()).toBe(true)
  })

  it('shows empty state when store has no orders', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = []
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('No orders')
  })

  it('renders an order card for each order in the store', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    await wrapper.vm.$nextTick()
    const cards = wrapper.findAll('.order-card')
    expect(cards.length).toBe(1)
  })

  it('displays item name on each order card', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    store.items = [MOCK_ITEMS[0]]
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('NMAT Review')
  })

  it('shows a detail link for each order', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    await wrapper.vm.$nextTick()
    const detailLink = wrapper.find('a[href="/candidate/orders/order-1"]')
    expect(detailLink.exists()).toBe(true)
  })

  it('shows payment link when order status is pending_payment', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    await wrapper.vm.$nextTick()
    const paymentLink = wrapper.find('a[href="/candidate/orders/order-1/payment"]')
    expect(paymentLink.exists()).toBe(true)
  })

  it('shows bargaining link when order is pending_payment with bargaining mode', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [{ ...MOCK_ORDER_BARGAINING, item_id: 'item-2' }]
    store.items = [MOCK_ITEMS[1]]
    await wrapper.vm.$nextTick()
    const bargainingLink = wrapper.find('a[href="/candidate/orders/order-2/bargaining"]')
    expect(bargainingLink.exists()).toBe(true)
  })

  it('does not show bargaining link for fixed-price pending_payment order', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    await wrapper.vm.$nextTick()
    const bargainingLink = wrapper.find('a[href="/candidate/orders/order-1/bargaining"]')
    expect(bargainingLink.exists()).toBe(false)
  })

  it('does not show empty state when orders are present', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING]
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).not.toContain('No orders')
  })

  it('shows multiple order cards for multiple orders', async () => {
    const wrapper = mount(OrderListView, { global: { plugins: [router] } })
    await flushPromises()
    const store = useOrderStore()
    store.orders = [MOCK_ORDER_PENDING, MOCK_ORDER_BARGAINING]
    await wrapper.vm.$nextTick()
    const cards = wrapper.findAll('.order-card')
    expect(cards.length).toBe(2)
  })
})
